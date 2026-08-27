import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import get_current_user
from app.db import get_db
from app.events.ics import generate_ics
from app.events.service import (
    create_event_service,
    get_events_range_service,
    get_or_create_default_calendar,
)
from app.invitations.service import create_rsvp_token, send_event_invitation
from app.models import Calendar, Event, EventAttendee, User
from app.schemas import (
    CalendarCreate,
    CalendarResponse,
    EventCreate,
    EventResponse,
    EventUpdate,
)

router = APIRouter(tags=["events"])


@router.get("/calendars", response_model=List[CalendarResponse])
async def list_calendars(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Ensure default calendar exists
    await get_or_create_default_calendar(db, current_user.id)
    stmt = select(Calendar).where(Calendar.owner_id == current_user.id).order_by(Calendar.created_at.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/calendars", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    payload: CalendarCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cal = Calendar(
        owner_id=current_user.id,
        name=payload.name,
        color=payload.color,
        is_default=False,
    )
    db.add(cal)
    await db.flush()
    return cal


@router.get("/events")
async def list_events(
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    calendar_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Default range: 30 days before to 90 days after if unspecified
    now = datetime.now(timezone.utc)
    start_range = from_date or (now - timedelta(days=30))
    end_range = to_date or (now + timedelta(days=90))

    instances = await get_events_range_service(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        from_date=start_range,
        to_date=end_range,
        calendar_id=calendar_id,
    )
    return instances


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event = await create_event_service(
        db=db,
        user=current_user,
        payload=payload,
        background_tasks=background_tasks,
    )
    return event


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Event)
        .options(selectinload(Event.attendees))
        .where(Event.id == event_id)
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Event)
        .options(selectinload(Event.attendees))
        .where(Event.id == event_id)
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only organizer can edit event")

    if payload.title is not None:
        event.title = payload.title
    if payload.description is not None:
        event.description = payload.description
    if payload.location is not None:
        event.location = payload.location
    if payload.start_at is not None:
        event.start_at = payload.start_at
    if payload.end_at is not None:
        event.end_at = payload.end_at
    if payload.all_day is not None:
        event.all_day = payload.all_day
    if payload.recurrence_rule is not None:
        event.recurrence_rule = payload.recurrence_rule
    if payload.reminder_minutes_before is not None:
        event.reminder_minutes_before = payload.reminder_minutes_before
    if payload.color is not None:
        event.color = payload.color
    if payload.meeting_link is not None:
        event.meeting_link = payload.meeting_link
    if payload.calendar_id is not None:
        event.calendar_id = payload.calendar_id

    # Handle attendees update
    if payload.attendees is not None:
        existing_emails = {a.email.lower() for a in event.attendees}
        for att in payload.attendees:
            if att.email.lower() not in existing_emails:
                token = create_rsvp_token()
                new_att = EventAttendee(
                    event_id=event.id,
                    user_id=att.user_id,
                    email=att.email,
                    attendee_type=att.attendee_type or "external",
                    rsvp_status="pending",
                    rsvp_token=token,
                )
                db.add(new_att)
                background_tasks.add_task(send_event_invitation, event, new_att, current_user.email)
                new_att.invitation_sent_at = datetime.now(timezone.utc)

    await db.flush()
    stmt = (
        select(Event)
        .options(selectinload(Event.attendees))
        .where(Event.id == event.id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).where(Event.id == event_id)
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only organizer can delete event")

    await db.delete(event)
    await db.flush()
    return None


@router.get("/events/{event_id}/ics")
async def download_event_ics(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Event)
        .options(selectinload(Event.attendees))
        .where(Event.id == event_id)
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user_stmt = select(User).where(User.id == event.organizer_id)
    user_res = await db.execute(user_stmt)
    organizer = user_res.scalar_one_or_none()
    organizer_email = organizer.email if organizer else "calendar@sidanex.com"

    ics_content = generate_ics(event, event.attendees, organizer_email)

    safe_title = "".join(c for c in event.title if c.isalnum() or c in ("-", "_")).rstrip()
    filename = f"{safe_title or 'event'}.ics"

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
