import secrets
from email.message import EmailMessage
import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.events.ics import generate_ics
from app.models import Event, EventAttendee, User


def create_rsvp_token() -> str:
    return secrets.token_urlsafe(24)


async def send_event_invitation(event: Event, attendee: EventAttendee, organizer_email: str):
    """
    Sends an async email invitation containing event details, Meet join link,
    1-click RSVP action buttons, and attached standard .ics file.
    """
    if not settings.EMAIL_INVITES_ENABLED or not settings.SMTP_HOST:
        print(f"[calendar-invitations] Skipping email delivery for {attendee.email} (SMTP not configured)")
        return

    try:
        # Build ICS attachment
        ics_data = generate_ics(event, event.attendees or [attendee], organizer_email)

        msg = EmailMessage()
        msg["Subject"] = f"Invitation: {event.title} @ {event.start_at.strftime('%a %b %d, %Y %I:%M %p')}"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = attendee.email

        rsvp_yes_url = f"{settings.FRONTEND_URL}/rsvp/{attendee.rsvp_token}?status=yes"
        rsvp_no_url = f"{settings.FRONTEND_URL}/rsvp/{attendee.rsvp_token}?status=no"
        rsvp_maybe_url = f"{settings.FRONTEND_URL}/rsvp/{attendee.rsvp_token}?status=maybe"

        formatted_time = f"{event.start_at.strftime('%A, %B %d, %Y')} · {event.start_at.strftime('%I:%M %p')} - {event.end_at.strftime('%I:%M %p')}"
        
        meet_section = ""
        if event.meeting_link:
            meet_section = f"""
            <div style="margin: 16px 0; padding: 14px; background: #e8f0fe; border-radius: 8px; display: inline-block;">
              <span style="font-weight: bold; color: #1a73e8;">📹 Join with Sidaz Meet:</span><br/>
              <a href="{event.meeting_link}" style="color: #1a73e8; font-weight: bold; word-break: break-all;">{event.meeting_link}</a>
            </div>
            """

        location_section = ""
        if event.location:
            location_section = f"<p style='color: #5f6368;'>📍 <strong>Location:</strong> {event.location}</p>"

        desc_section = ""
        if event.description:
            desc_section = f"<div style='margin-top: 12px; color: #3c4043; line-height: 1.5;'>{event.description}</div>"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8f9fa; padding: 24px; margin: 0;">
          <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #dadce0; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(60,64,67,0.1);">
            <div style="background: #1a73e8; padding: 18px 24px; color: #ffffff;">
              <h1 style="margin: 0; font-size: 20px; font-weight: 500;">Meridian Calendar Invitation</h1>
            </div>
            
            <div style="padding: 24px;">
              <h2 style="margin-top: 0; color: #202124; font-size: 22px;">{event.title}</h2>
              <p style="color: #5f6368; font-size: 15px; margin: 8px 0;">🗓️ <strong>When:</strong> {formatted_time}</p>
              {location_section}
              {meet_section}
              {desc_section}
              
              <div style="margin-top: 28px; padding-top: 20px; border-top: 1px solid #eeeeee;">
                <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #202124;">Going?</p>
                <div>
                  <a href="{rsvp_yes_url}" style="display: inline-block; padding: 10px 20px; background: #1a73e8; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 500; margin-right: 8px;">Yes</a>
                  <a href="{rsvp_maybe_url}" style="display: inline-block; padding: 10px 20px; background: #f1f3f4; color: #3c4043; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 500; margin-right: 8px;">Maybe</a>
                  <a href="{rsvp_no_url}" style="display: inline-block; padding: 10px 20px; background: #f1f3f4; color: #3c4043; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 500;">No</a>
                </div>
              </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 12px 24px; border-top: 1px solid #dadce0; font-size: 12px; color: #70757a; text-align: center;">
              Sent by Meridian Calendar · An .ics calendar file is attached for importing.
            </div>
          </div>
        </body>
        </html>
        """

        msg.set_content(f"Invitation: {event.title} on {formatted_time}\nJoin Link: {event.meeting_link or 'N/A'}\nRSVP Yes: {rsvp_yes_url}\nRSVP No: {rsvp_no_url}")
        msg.add_alternative(html_body, subtype="html")
        msg.add_attachment(ics_data, maintype="text", subtype="calendar", filename=f"invite-{event.id}.ics")

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
            timeout=10.0,
        )
        print(f"[calendar-invitations] Invitation email sent to {attendee.email}")
    except Exception as e:
        print(f"[calendar-invitations] Failed to send email invitation: {e}")
