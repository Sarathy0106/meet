import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_db
from app.models import Event, InAppNotification, PushSubscription, User
from app.notifications.service import create_in_app_notification, dispatch_web_push, send_reminder_email
from app.schemas import InAppNotificationResponse, PushSubscriptionCreate

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=List[InAppNotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(InAppNotification)
        .where(InAppNotification.user_id == current_user.id)
        .order_by(InAppNotification.created_at.desc())
        .limit(50)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        update(InAppNotification)
        .where(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == current_user.id,
        )
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.flush()
    return {"success": True}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        update(InAppNotification)
        .where(InAppNotification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.flush()
    return {"success": True}


@router.post("/notifications/push-subscription", status_code=status.HTTP_201_CREATED)
async def register_push_subscription(
    payload: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.user_id = current_user.id
        existing.p256dh = payload.p256dh
        existing.auth = payload.auth
    else:
        sub = PushSubscription(
            user_id=current_user.id,
            endpoint=payload.endpoint,
            p256dh=payload.p256dh,
            auth=payload.auth,
        )
        db.add(sub)

    await db.flush()
    return {"success": True, "message": "Push subscription registered"}


@router.delete("/notifications/push-subscription")
async def unregister_push_subscription(
    payload: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PushSubscription).where(
        PushSubscription.endpoint == payload.endpoint,
        PushSubscription.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    if sub:
        await db.delete(sub)
        await db.flush()
    return {"success": True}


@router.post("/events/{event_id}/remind")
async def trigger_event_reminder(
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

    title = f"Reminder: {event.title}"
    body = f"Starts at {event.start_at.strftime('%I:%M %p')}"

    # In-app notification
    await create_in_app_notification(db, str(current_user.id), title, body, str(event.id))

    # Push notification
    background_tasks.add_task(dispatch_web_push, db, str(current_user.id), title, body, event.meeting_link)

    # Email reminders to attendees
    for att in event.attendees:
        background_tasks.add_task(send_reminder_email, event, att.email)
        att.reminder_sent_at = datetime.now(timezone.utc)

    await db.flush()
    return {"success": True, "message": "Reminders dispatched"}
