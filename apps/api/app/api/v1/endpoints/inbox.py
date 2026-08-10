from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.inbox import (
    ConversationListItem,
    ConversationResponse,
    MessageResponse,
    MessageTemplateSummary,
    SendMessageRequest,
    StartConversationRequest,
)
from app.services.inbox import (
    get_conversation,
    get_conversations,
)
from app.services.messages import (
    normalize_phone_number,
    render_template_body,
    send_outbound_message,
    send_template_message,
)
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
)
from app.services.realtime import realtime_manager
from app.services.whatsapp import get_connections

router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"],
)


def _describe_meta_error(exc: httpx.HTTPStatusError) -> str:
    try:
        message = exc.response.json().get(
            "error", {}
        ).get("message")
    except ValueError:
        message = None

    if message:
        return f"WhatsApp API error: {message}"

    return (
        "WhatsApp API error: "
        f"{exc.response.status_code}"
    )


@router.get(
    "/conversations",
    response_model=list[ConversationListItem],
)
def list_conversations(
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    conversations = get_conversations(
        db,
        organization_id=(
            current_user.organization_id
        ),
    )

    result = []

    for conversation in conversations:
        messages = sorted(
            conversation.messages,
            key=lambda message: (
                message.created_at
            ),
            reverse=True,
        )

        result.append(
            ConversationListItem(
                id=conversation.id,
                whatsapp_connection_id=(
                    conversation.whatsapp_connection_id
                ),
                customer_phone_number=(
                    conversation.customer_phone_number
                ),
                last_message=(
                    MessageResponse.model_validate(
                        messages[0]
                    )
                    if messages
                    else None
                ),
                unread_count=(
                    conversation.unread_count
                ),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
        )

    return result


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
def get_single_conversation(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    conversation = get_conversation(
        db,
        organization_id=(
            current_user.organization_id
        ),
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    conversation.messages.sort(
        key=lambda message: message.created_at
    )

    return conversation


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def list_conversation_messages(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.organization_id
            == current_user.organization_id,
            Conversation.deleted_at.is_(None),
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return db.scalars(
        select(Message)
        .where(
            Message.conversation_id
            == conversation_id,
        )
        .order_by(Message.created_at.asc())
    ).all()


@router.post(
    "/conversations/{conversation_id}/read",
)
def mark_conversation_read(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.organization_id
            == current_user.organization_id,
            Conversation.deleted_at.is_(None),
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    conversation.unread_count = 0

    db.commit()
    db.refresh(conversation)

    return {
        "conversation_id": str(conversation.id),
        "unread_count": conversation.unread_count,
    }


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
)
async def send_message(
    conversation_id: UUID,
    payload: SendMessageRequest,
    current_user: CurrentUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.organization_id
            == current_user.organization_id,
            Conversation.deleted_at.is_(None),
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    if (
        conversation.whatsapp_connection
        is None
        or not conversation.whatsapp_connection.is_active
    ):
        raise HTTPException(
            status_code=409,
            detail="WhatsApp connection is not active",
        )

    text = payload.text.strip()

    try:
        message = await send_outbound_message(
            db,
            organization_id=(
                current_user.organization_id
            ),
            conversation=conversation,
            text=text,
        )

        db.commit()
        db.refresh(message)

    except httpx.HTTPStatusError as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=_describe_meta_error(exc),
        ) from exc

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    await realtime_manager.broadcast_to_organization(
        current_user.organization_id,
        {
            "type": "message_created",
            "conversation_id": str(conversation.id),
            "message": MessageResponse.model_validate(
                message
            ).model_dump(mode="json"),
        },
    )

    return message


def _get_active_connection(
    db: Session,
    *,
    organization_id: UUID,
):
    connections = get_connections(
        db,
        organization_id,
    )

    if not connections:
        raise HTTPException(
            status_code=409,
            detail=(
                "No active WhatsApp connection"
                " configured"
            ),
        )

    return connections[0]


@router.get(
    "/templates",
    response_model=list[MessageTemplateSummary],
)
async def list_message_templates(
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    connection = _get_active_connection(
        db,
        organization_id=(
            current_user.organization_id
        ),
    )

    access_token = token_encryption.decrypt(
        connection.access_token_encrypted
    )

    client = MetaWhatsAppClient()

    try:
        templates = (
            await client.get_message_templates(
                waba_id=connection.waba_id,
                access_token=access_token,
            )
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=_describe_meta_error(exc),
        ) from exc

    return [
        MessageTemplateSummary(
            name=template.name,
            language=template.language,
            category=template.category,
            body_text=template.body_text,
            placeholder_count=(
                template.placeholder_count
            ),
        )
        for template in templates
    ]


@router.post(
    "/conversations",
    response_model=ConversationResponse,
)
async def start_conversation(
    payload: StartConversationRequest,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    connection = _get_active_connection(
        db,
        organization_id=(
            current_user.organization_id
        ),
    )

    customer_phone_number = (
        normalize_phone_number(
            payload.customer_phone_number,
        )
    )

    if not customer_phone_number:
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number",
        )

    access_token = token_encryption.decrypt(
        connection.access_token_encrypted
    )

    client = MetaWhatsAppClient()

    try:
        templates = (
            await client.get_message_templates(
                waba_id=connection.waba_id,
                access_token=access_token,
            )
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=_describe_meta_error(exc),
        ) from exc

    template = next(
        (
            item
            for item in templates
            if item.name == payload.template_name
        ),
        None,
    )

    if template is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Template not found or not approved"
            ),
        )

    if (
        len(payload.parameters)
        != template.placeholder_count
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Expected "
                f"{template.placeholder_count} "
                "template parameter(s), got "
                f"{len(payload.parameters)}"
            ),
        )

    rendered_text = render_template_body(
        template.body_text,
        payload.parameters,
    )

    try:
        message = await send_template_message(
            db,
            organization_id=(
                current_user.organization_id
            ),
            whatsapp_connection=connection,
            customer_phone_number=(
                customer_phone_number
            ),
            template_name=payload.template_name,
            language_code=payload.language_code,
            parameters=payload.parameters,
            rendered_text=rendered_text,
        )

        db.commit()

    except httpx.HTTPStatusError as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=_describe_meta_error(exc),
        ) from exc

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    conversation = get_conversation(
        db,
        organization_id=(
            current_user.organization_id
        ),
        conversation_id=message.conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=500,
            detail="Conversation not found after send",
        )

    conversation.messages.sort(
        key=lambda item: item.created_at
    )

    return conversation