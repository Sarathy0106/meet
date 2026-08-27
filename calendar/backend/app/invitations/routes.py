import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_db
from app.invitations.service import send_event_invitation
from app.models import Event, EventAttendee, User
from app.schemas import RSVPRequest

router = APIRouter(tags=["invitations"])


@router.post("/events/{event_id}/invite")
async def resend_invitations(
    event_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).where(Event.id == event_id)
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only event organizer can send invitations")

    count = 0
    for attendee in event.attendees:
        background_tasks.add_task(send_event_invitation, event, attendee, current_user.email)
        attendee.invitation_sent_at = datetime.now(timezone.utc)
        count += 1

    await db.flush()
    return {"success": True, "invitations_dispatched": count}


@router.post("/events/{event_id}/rsvp")
async def user_rsvp(
    event_id: uuid.UUID,
    payload: RSVPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        (EventAttendee.user_id == current_user.id) | (EventAttendee.email == current_user.email),
    )
    res = await db.execute(stmt)
    attendee = res.scalar_one_or_none()

    if not attendee:
        # Create attendee entry for this user
        attendee = EventAttendee(
            event_id=event_id,
            user_id=current_user.id,
            email=current_user.email,
            attendee_type="internal",
            rsvp_status=payload.status,
        )
        db.add(attendee)
    else:
        attendee.rsvp_status = payload.status

    await db.flush()
    return {"success": True, "rsvp_status": attendee.rsvp_status}


@router.get("/rsvp/{token}")
async def get_rsvp_info(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EventAttendee).where(EventAttendee.rsvp_token == token)
    res = await db.execute(stmt)
    attendee = res.scalar_one_or_none()

    if not attendee:
        raise HTTPException(status_code=404, detail="Invalid or expired RSVP token")

    event_stmt = select(Event).where(Event.id == attendee.event_id)
    event_res = await db.execute(event_stmt)
    event = event_res.scalar_one_or_none()

    return {
        "event_id": str(attendee.event_id),
        "event_title": event.title if event else "Calendar Event",
        "start_at": event.start_at.isoformat() if event else None,
        "end_at": event.end_at.isoformat() if event else None,
        "meeting_link": event.meeting_link if event else None,
        "attendee_email": attendee.email,
        "current_rsvp_status": attendee.rsvp_status,
    }


@router.post("/rsvp/{token}")
async def public_rsvp_by_token(
    token: str,
    status: str = Query(..., pattern="^(yes|no|maybe)$"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EventAttendee).where(EventAttendee.rsvp_token == token)
    res = await db.execute(stmt)
    attendee = res.scalar_one_or_none()

    if not attendee:
        raise HTTPException(status_code=404, detail="Invalid or expired RSVP token")

    attendee.rsvp_status = status
    await db.flush()

    return {
        "success": True,
        "email": attendee.email,
        "status": attendee.rsvp_status,
        "message": f"Thank you! Your RSVP status has been recorded as '{status}'.",
    }
