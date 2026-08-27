import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.events.service import get_or_create_default_calendar
from app.models import Event
from app.schemas import InternalEventCreate

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_event_from_meet(
    payload: InternalEventCreate,
    x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key"),
    db: AsyncSession = Depends(get_db),
):
    if x_internal_api_key != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service key",
        )

    organizer_id = payload.organizer_id or uuid.uuid4()
    default_cal = await get_or_create_default_calendar(db, organizer_id)

    event = Event(
        calendar_id=default_cal.id,
        organizer_id=organizer_id,
        title=payload.title,
        description=payload.description,
        start_at=payload.start_at,
        end_at=payload.end_at,
        meeting_id=payload.meeting_id,
        meeting_link=payload.meeting_link,
        source="meet",
        color="#1a73e8",
    )
    db.add(event)
    await db.flush()

    return {
        "id": str(event.id),
        "title": event.title,
        "start_at": event.start_at.isoformat(),
        "end_at": event.end_at.isoformat(),
        "meeting_link": event.meeting_link,
        "source": "meet",
    }
