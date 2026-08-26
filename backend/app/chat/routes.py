from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import get_optional_current_user
from app.db import get_db
from app.meetings.service import get_meeting_by_code
from app.models import ChatMessage, User
from app.schemas import ChatMessageCreate, ChatMessageResponse

router = APIRouter(prefix="/meetings/{code}/chat", tags=["chat"])


@router.get("", response_model=List[ChatMessageResponse])
async def get_meeting_chat(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.meeting_id == meeting.id)
        .order_by(ChatMessage.sent_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [ChatMessageResponse.model_validate(msg) for msg in messages]


@router.post("", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def post_meeting_chat(
    code: str,
    chat_in: ChatMessageCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    sender_name = chat_in.sender_name
    sender_id = chat_in.sender_id
    if current_user:
        sender_name = current_user.display_name
        sender_id = f"user_{current_user.id}"

    new_message = ChatMessage(
        meeting_id=meeting.id,
        sender_name=sender_name,
        sender_id=sender_id,
        content=chat_in.content.strip(),
    )
    db.add(new_message)
    await db.flush()
    await db.refresh(new_message)

    return ChatMessageResponse.model_validate(new_message)
