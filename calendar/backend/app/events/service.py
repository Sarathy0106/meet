import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.events.recurrence import expand_event_recurrence
from app.invitations.service import create_rsvp_token, send_event_invitation
from app.meet_client import create_meet_meeting
from app.models import Calendar, Event, EventAttendee, User
from app.schemas import EventCreate, EventUpdate


async def get_or_create_default_calendar(db: AsyncSession, owner_id: uuid.UUID) -> Calendar:
    stmt = select(Calendar).where(Calendar.owner_id == owner_id, Calendar.is_default == True)
    res = await db.execute(stmt)
    cal = res.scalar_one_or_none()
    if not cal:
        cal = Calendar(
            owner_id=owner_id,
            name="My Calendar",
            color="#4285F4",
            is_default=True,
        )
        db.add(cal)
        await db.flush()
    return cal


async def create_event_service(
    db: AsyncSession,
    user: User,
    payload: EventCreate,
    background_tasks = None,
) -> Event:
    calendar_id = payload.calendar_id
    if not calendar_id:
        default_cal = await get_or_create_default_calendar(db, user.id)
        calendar_id = default_cal.id

    meeting_id = None
    meeting_link = None
    if payload.add_video:
        meet_res = await create_meet_meeting(
            title=payload.title,
            start_at=payload.start_at,
            organizer_id=str(user.id),
        )
        meeting_link = meet_res.get("join_url")
        if meet_res.get("id"):
            try:
                meeting_id = uuid.UUID(meet_res["id"])
            except Exception:
                pass

    event = Event(
        calendar_id=calendar_id,
        organizer_id=user.id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        start_at=payload.start_at,
        end_at=payload.end_at,
        all_day=payload.all_day,
        recurrence_rule=payload.recurrence_rule,
        reminder_minutes_before=payload.reminder_minutes_before or 10,
        meeting_id=meeting_id,
        meeting_link=meeting_link,
        source="calendar",
        color=payload.color or "#4285F4",
    )
    db.add(event)
    await db.flush()

    # Add organizer as attendee (accepted)
    org_attendee = EventAttendee(
        event_id=event.id,
        user_id=user.id,
        email=user.email,
        attendee_type="internal",
        rsvp_status="yes",
        rsvp_token=create_rsvp_token(),
    )
    db.add(org_attendee)

    # Add other attendees
    if payload.attendees:
        for att in payload.attendees:
            if att.email.lower() == user.email.lower():
                continue
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
            if background_tasks:
                background_tasks.add_task(send_event_invitation, event, new_att, user.email)
                new_att.invitation_sent_at = datetime.now(timezone.utc)

    await db.flush()

    # Eagerly load event with attendees so Pydantic serialization doesn't trigger async greenlet error
    stmt = (
        select(Event)
        .options(selectinload(Event.attendees))
        .where(Event.id == event.id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


async def get_events_range_service(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_email: str,
    from_date: datetime,
    to_date: datetime,
    calendar_id: Optional[uuid.UUID] = None,
) -> List[dict]:
    stmt = (
        select(Event)
        .options(selectinload(Event.attendees))
        .where(
            or_(
                Event.organizer_id == user_id,
                Event.attendees.any(EventAttendee.email == user_email),
                Event.attendees.any(EventAttendee.user_id == user_id),
            )
        )
    )

    if calendar_id:
        stmt = stmt.where(Event.calendar_id == calendar_id)

    res = await db.execute(stmt)
    events = res.scalars().unique().all()

    all_instances = []
    for ev in events:
        instances = expand_event_recurrence(ev, from_date, to_date)
        all_instances.extend(instances)

    # Sort by start_at
    all_instances.sort(key=lambda x: x["start_at"])
    return all_instances
