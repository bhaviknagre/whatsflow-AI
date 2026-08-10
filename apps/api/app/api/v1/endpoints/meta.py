from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from app.core.config import settings
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.schemas.whatsapp import (
    MetaConnectResponse,
    MetaSignupRequest,
    MetaSignupResponse,
)
from app.services.meta_connection import (
    MetaConnectionService,
)
from app.services.meta_oauth import (
    consume_oauth_state,
    create_oauth_state,
)

router = APIRouter(
    prefix="/meta",
    tags=["Meta"],
)


@router.get(
    "/whatsapp/connect",
    response_model=MetaConnectResponse,
)
def connect_whatsapp(
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    if not settings.META_APP_ID:
        raise HTTPException(
            status_code=503,
            detail=(
                "Meta integration is not configured"
            ),
        )

    if not settings.META_EMBEDDED_SIGNUP_CONFIG_ID:
        raise HTTPException(
            status_code=503,
            detail=(
                "Meta Embedded Signup "
                "is not configured"
            ),
        )

    state = create_oauth_state(
        db=db,
        organization_id=current_user.organization_id,
    )

    return MetaConnectResponse(
        state=state,
    )


@router.post(
    "/whatsapp/signup",
    response_model=MetaSignupResponse,
)
async def complete_whatsapp_signup(
    payload: MetaSignupRequest,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    try:
        organization_id = consume_oauth_state(
            db=db,
            state_value=payload.state,
        )
    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if (
        organization_id
        != current_user.organization_id
    ):
        db.rollback()

        raise HTTPException(
            status_code=403,
            detail=(
                "Signup state does not belong "
                "to organization"
            ),
        )

    try:
        service = MetaConnectionService()

        connection = (
            await service.exchange_and_validate(
                code=payload.code,
                waba_id=payload.waba_id,
                phone_number_id=(
                    payload.phone_number_id
                ),
            )
        )

        existing = db.scalar(
            select(WhatsAppConnection)
            .where(
                WhatsAppConnection.phone_number_id
                == connection.phone_number_id
            )
        )

        encrypted_token = (
            token_encryption.encrypt(
                connection.access_token
            )
        )

        if existing:
            if (
                existing.organization_id
                != current_user.organization_id
            ):
                db.rollback()

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This WhatsApp number "
                        "is already connected "
                        "to another organization."
                    ),
                )

            existing.waba_id = (
                connection.waba_id
            )
            existing.display_phone_number = (
                connection.display_phone_number
            )
            existing.verified_name = (
                connection.verified_name
            )
            existing.access_token_encrypted = (
                encrypted_token
            )
            existing.expires_at = (
                connection.expires_at
            )
            existing.is_active = True

            db.commit()
            db.refresh(existing)

            connection_id = existing.id

        else:
            whatsapp_connection = (
                WhatsAppConnection(
                    organization_id=(
                        current_user.organization_id
                    ),
                    waba_id=connection.waba_id,
                    phone_number_id=(
                        connection.phone_number_id
                    ),
                    display_phone_number=(
                        connection.display_phone_number
                    ),
                    verified_name=(
                        connection.verified_name
                    ),
                    access_token_encrypted=(
                        encrypted_token
                    ),
                    expires_at=(
                        connection.expires_at
                    ),
                    is_active=True,
                )
            )

            db.add(whatsapp_connection)
            db.commit()
            db.refresh(whatsapp_connection)

            connection_id = (
                whatsapp_connection.id
            )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to complete "
                "Meta WhatsApp signup"
            ),
        ) from exc

    return MetaSignupResponse(
        status="connected",
        connection_id=connection_id,
    )