import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.meetings.service import create_unique_meeting
from app.models import User
from app.schemas import MeetingCreate

router = APIRouter(prefix="/internal", tags=["internal"])


class InternalMeetingCreateRequest(BaseModel):
    title: str = "Scheduled Meeting"
    scheduled_at: Optional[datetime] = None
    organizer_id: Optional[uuid.UUID] = None


class InternalMeetingResponse(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    scheduled_at: Optional[datetime] = None
    join_url: str


@router.post("/meetings", response_model=InternalMeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_meeting(
    payload: InternalMeetingCreateRequest,
    x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key"),
    db: AsyncSession = Depends(get_db),
):
    if x_internal_api_key != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service key",
        )

    host_user = None
    if payload.organizer_id:
        stmt = select(User).where(User.id == payload.organizer_id)
        result = await db.execute(stmt)
        host_user = result.scalar_one_or_none()

    meeting_in = MeetingCreate(
        title=payload.title,
        scheduled_at=payload.scheduled_at,
        lobby_enabled=True,
    )

    meeting = await create_unique_meeting(db, host=host_user, meeting_in=meeting_in)

    join_url = f"{settings.FRONTEND_URL}/meet/{meeting.code}"

    return InternalMeetingResponse(
        id=meeting.id,
        code=meeting.code,
        title=meeting.title,
        scheduled_at=meeting.scheduled_at,
        join_url=join_url,
    )
