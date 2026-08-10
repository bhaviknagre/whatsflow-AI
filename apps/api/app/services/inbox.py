from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation


def get_conversations(
    db: Session,
    *,
    organization_id: UUID,
) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(
                Conversation.organization_id
                == organization_id,
                Conversation.deleted_at.is_(None),
            )
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .order_by(
                Conversation.updated_at.desc()
            )
        )
    )


def get_conversation(
    db: Session,
    *,
    organization_id: UUID,
    conversation_id: UUID,
) -> Conversation | None:
    return db.scalar(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.organization_id
            == organization_id,
            Conversation.deleted_at.is_(None),
        )
        .options(
            selectinload(
                Conversation.whatsapp_connection
            ),
            selectinload(
                Conversation.messages
            ),
        )
    )
