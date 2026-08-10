from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation

router = APIRouter(tags=["Conversations"])


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == current_user.organization_id,
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return {
        "id": str(conversation.id),
        "organization_id": str(conversation.organization_id),
    }
