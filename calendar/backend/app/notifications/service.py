import json
from email.message import EmailMessage
import aiosmtplib
from pywebpush import webpush, WebPushException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Event, InAppNotification, PushSubscription, User


async def create_in_app_notification(db: AsyncSession, user_id: str, title: str, message: str, event_id: str = None) -> InAppNotification:
    notif = InAppNotification(
        user_id=user_id,
        event_id=event_id,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(notif)
    await db.flush()
    return notif


async def dispatch_web_push(db: AsyncSession, user_id: str, title: str, body: str, event_url: str = None):
    """
    Sends browser push notifications to all registered device endpoints for a user.
    """
    if not settings.PUSH_NOTIFICATIONS_ENABLED or not settings.VAPID_PRIVATE_KEY:
        return

    stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
    res = await db.execute(stmt)
    subscriptions = res.scalars().all()

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": event_url or settings.FRONTEND_URL,
        "icon": "/icons/calendar-192.png",
        "badge": "/icons/badge-72.png",
    })

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                timeout=5,
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code in (404, 410):
                # Subscription expired or revoked, remove from DB
                await db.delete(sub)
            print(f"[calendar-push] WebPush error: {ex}")
        except Exception as e:
            print(f"[calendar-push] Unexpected push error: {e}")

    await db.flush()


async def send_reminder_email(event: Event, attendee_email: str):
    """
    Dispatches pre-event reminder email to an attendee.
    """
    if not settings.EMAIL_REMINDERS_ENABLED or not settings.SMTP_HOST:
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = f"Reminder: {event.title} starts soon"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = attendee_email

        formatted_time = f"{event.start_at.strftime('%I:%M %p')} ({event.start_at.strftime('%A, %B %d, %Y')})"
        
        meet_button = ""
        if event.meeting_link:
            meet_button = f"""
            <div style="margin: 20px 0;">
              <a href="{event.meeting_link}" style="display: inline-block; padding: 12px 24px; background: #1a73e8; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold;">Join with Sidaz Meet</a>
            </div>
            """

        html_body = f"""
        <div style="font-family: sans-serif; max-width: 580px; margin: 0 auto; padding: 24px; border: 1px solid #dadce0; border-radius: 12px;">
          <h2 style="color: #202124; margin-top: 0;">Reminder: {event.title}</h2>
          <p style="color: #5f6368; font-size: 15px;">Starts at <strong>{formatted_time}</strong></p>
          {f'<p>📍 Location: {event.location}</p>' if event.location else ''}
          {meet_button}
          <p style="color: #70757a; font-size: 12px; margin-top: 24px;">Sent by Meridian Calendar</p>
        </div>
        """

        msg.set_content(f"Reminder: {event.title} starts at {formatted_time}. Join: {event.meeting_link or 'N/A'}")
        msg.add_alternative(html_body, subtype="html")

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
            timeout=10.0,
        )
    except Exception as e:
        print(f"[calendar-reminders] Failed to send reminder email: {e}")
