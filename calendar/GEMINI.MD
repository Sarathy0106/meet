# Calendar (Meridian) — Technical Build Specification

### with Meet Clone Integration, ICS Export, Email Invites & Multi-Channel Reminders

A digital twin of Google Calendar, built on the same stack as the Meet Clone, wired together
so scheduling a meeting automatically produces a calendar event with a join link — and
creating a calendar event with "Add video conferencing" automatically produces a Meet meeting.
Includes standard `.ics` calendar file export/download, external email invitations with attached
`.ics` files, and multi-channel reminders (in-app, email, and Web browser push notifications).

This assumes the Meet Clone spec (`meet-clone-spec.md`) is already built and deployed as its
own service. Calendar is a **separate service** that talks to it over HTTP — same pattern
Zoho uses between Zoho Calendar and Zoho Meet.

---

## 1. High-Level Architecture

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  Vue 3 SPA (Calendar FE) │         │  Vue 3 SPA (Meet FE)     │
│  Deployed on Vercel      │         │  Deployed on Vercel      │
└───────────┬───────────────┘         └────────────┬─────────────┘
            │ REST                                  │ REST
            ▼                                       ▼
┌──────────────────────────┐  internal   ┌──────────────────────────┐
│  FastAPI (Calendar BE)   │◄───REST────►│  FastAPI (Meet BE)       │
│  Deployed on Vercel      │  API-key    │  Deployed on Vercel      │
└───────────┬───────────────┘  auth      └────────────┬─────────────┘
            │ SQL                                     │ SQL
            ▼                                         ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│  Neon Postgres            │              │  Neon Postgres            │
│  (calendar DB, own schema)│              │  (meet DB — already built)│
└──────────────────────────┘              └──────────────────────────┘

```

**Two independent services, not a merged backend.** Calendar owns `events`, `attendees`,
`push_subscriptions`, and `notifications`. Meet owns `meetings`, `meeting_participants`,
`chat_messages` (already built). They call each other's REST APIs using a shared internal
API key — same approach the rest of your Sidanex ecosystem uses between products (e.g. Pulse ↔ Sidaz Connect).
This keeps each product independently deployable.

### Integration flow (both directions)

**A. Scheduling from the Meet dashboard → shows up on Calendar**

1. User schedules a meeting in the Meet app (title, date/time).
2. Meet backend creates the `meetings` row as usual.
3. Meet backend calls `POST {CALENDAR_API_URL}/internal/events` on the Calendar service with the title, start/end time, organizer, and the meeting join link.
4. Calendar backend creates an `events` row with `meeting_id` + `meeting_link` populated, `source = 'meet'`.
5. It now appears on the user's calendar grid like any other event, with a "Join" button.

**B. Creating an event on Calendar with "Add video conferencing" → creates a Meet meeting**

1. User creates a calendar event and toggles "Add video conferencing."
2. Calendar backend calls `POST {MEET_API_URL}/internal/meetings` on the Meet service with the title and scheduled time.
3. Meet backend creates the `meetings` row, returns `{ code, join_url }`.
4. Calendar backend stores `meeting_id`, `meeting_link` on its own `events` row, `source = 'calendar'`.
5. Event detail view shows the "Join" button using that link.

**Whichever side initiates, the other side ends up with a matching, linked record** — no
duplication, single source of truth per meeting (the Meet DB always owns the canonical
meeting; Calendar just stores a reference + link for display).

### Internal service-to-service auth

Both backends accept a shared secret header on `/internal/*` routes only:

```http
X-Internal-Api-Key: <INTERNAL_SERVICE_KEY>
```

This is separate from user-facing JWT auth. Never expose `/internal/*` routes to the frontend;
only the two backends call them, server-to-server.

---

## 2. Tech Stack (identical to Meet Clone)

| Layer | Technology |
| --- | --- |
| **Frontend framework** | Vue 3 (Composition API) + Vite |
| **Frontend state** | Pinia |
| **Frontend routing** | Vue Router |
| **Frontend styling** | Tailwind CSS |
| **Frontend icons** | `lucide-vue-next` |
| **Backend framework** | FastAPI (Python 3.11+) |
| **Backend deploy target** | Vercel Serverless Functions (Python runtime) |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic |
| **DB driver** | `asyncpg` |
| **Database (prod)** | Neon Postgres — separate project/database from Meet's |
| **Database (local)** | Postgres 16 via Docker Compose |
| **Auth (user-facing)** | JWT (access + refresh), shared user accounts if using SSO (see §7) |
| **Auth (service-to-service)** | Static internal API key via `X-Internal-Api-Key` header |
| **HTTP client (backend→backend)** | `httpx` (async) |
| **Calendar File Export (.ics)** | `icalendar` (RFC 5545 compliance) |
| **Email Invitations & Reminders** | `aiosmtplib` (asynchronous SMTP) |
| **Web Browser Push Notifications** | `pywebpush` (VAPID protocol) |
| **Hosting** | Vercel — its own project, `meet-clone-*` and `meridian-*` side by side |

---

## 3. Core Feature List

### 3.1 Views

- **Month view, week view, day view** with time-grid rendering
- **"Today" jump**, previous/next period navigation, date selector
- **Mini date picker sidebar** with month overview and jump-to-date
- **Timezone support** for global scheduling

### 3.2 Events & Scheduling

- **Create event:** title, description, start/end datetime, all-day toggle, location (text or address)
- **"Add video conferencing" toggle:** triggers automatic Meet meeting creation (see §1 Flow B)
- **Edit / delete event:** organizer permissions and cascade cancellation
- **Color-coding:** customizable per event or per calendar
- **Recurring events:** recurrence rules (daily, weekly, monthly, custom days, end date/count) — stored as an RRULE string and expanded server-side across requested date ranges
- **Meeting detail drawer / modal:** shows live status, meeting link, and attendee RSVPs

### 3.3 Attendees & External Invitations

- **Attendee management:** add by email (both internal registered users and external guests)
- **RSVP statuses:** `pending`, `yes`, `no`, `maybe` with direct RSVP actions from web or email link
- **External email invitations:**
  - Automatically generates and sends HTML email invitations to external attendees upon event creation/update
  - Includes event title, date/time, organizer name, description, meeting join URL, and RSVP buttons
  - Embeds standard `.ics` (iCalendar) attachment for one-click add to Google Calendar, Apple Calendar, Outlook, etc.
- **Asynchronous invitation delivery:** email dispatch runs via background tasks so event creation API responses remain instant (<150ms)

### 3.4 Standard iCalendar (.ics) Generation & Export

- **Downloadable `.ics` files:** `GET /events/{id}/ics` generates RFC 5545 compliant `.ics` files
- Contains:
  - `UID`, `DTSTAMP`, `DTSTART`, `DTEND`
  - `SUMMARY`, `DESCRIPTION`, `LOCATION`
  - `ORGANIZER` with mailto address
  - `ATTENDEE` list with RSVP roles
  - `URL` linking directly to the Meet video room
  - `STATUS:CONFIRMED`
  - `BEGIN:VALARM` / `ACTION:DISPLAY` for calendar reminders

### 3.5 Multi-Channel Reminders

- **Configurable reminder offsets:** 5m, 10m, 15m, 30m, 1h, 1d before the event (`reminder_minutes_before`)
- **In-app notifications:** displays in-app toast alerts and notification drawer items when approaching an event
- **Email reminders:** automated asynchronous reminder emails sent to attendees prior to event start
- **Browser push notifications:** Web Push API notifications delivered to the user's desktop/mobile browser even when the tab is backgrounded
- **Delivery tracking:** records `invitation_sent_at` and `reminder_sent_at` timestamps to ensure idempotency and prevent duplicate deliveries

### 3.6 Meet Integration Surface

- Event detail panel displays a prominent **Join with Sidaz Meet** button when `meeting_link` is set
- Meet's scheduled-meeting creation screen notes: "This meeting is synced to your Meridian Calendar"
- Calendar's event creation dialog displays the generated Meet code and direct join URL

### 3.7 Multiple Calendars (Stretch/Supported)

- "My Calendar" default; ability to create additional named calendars (e.g. "Work", "Personal") and toggle visibility

---

## 4. Data Model (Postgres — Calendar's own DB)

```sql
-- calendars (supports multiple calendars per user)
CREATE TABLE calendars (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id    UUID NOT NULL,              -- references Meet/shared users table by id (no FK across DBs)
  name        TEXT NOT NULL DEFAULT 'My Calendar',
  color       TEXT DEFAULT '#4285F4',
  is_default  BOOLEAN DEFAULT true,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- events
CREATE TABLE events (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  calendar_id             UUID REFERENCES calendars(id) ON DELETE CASCADE,
  organizer_id            UUID NOT NULL,           -- shared user id
  title                   TEXT NOT NULL,
  description             TEXT,
  location                TEXT,
  start_at                TIMESTAMPTZ NOT NULL,
  end_at                  TIMESTAMPTZ NOT NULL,
  all_day                 BOOLEAN DEFAULT false,
  recurrence_rule         TEXT,                   -- e.g. 'FREQ=WEEKLY;UNTIL=20261231', null if one-off
  reminder_minutes_before INTEGER DEFAULT 10,
  meeting_id              UUID,                    -- id of the row in Meet's DB, nullable
  meeting_link            TEXT,                    -- cached join URL, nullable
  source                  TEXT CHECK (source IN ('calendar','meet')) DEFAULT 'calendar',
  created_at              TIMESTAMPTZ DEFAULT now(),
  updated_at              TIMESTAMPTZ DEFAULT now()
);

-- event_attendees (supports internal and external attendees)
CREATE TABLE event_attendees (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id            UUID REFERENCES events(id) ON DELETE CASCADE,
  user_id             UUID NULL,              -- shared user id for internal users
  email               TEXT NOT NULL,          -- works for both internal and external attendees
  attendee_type       TEXT CHECK (
                          attendee_type IN ('internal', 'external')
                        ) DEFAULT 'external',
  rsvp_status         TEXT CHECK (
                          rsvp_status IN ('pending','yes','no','maybe')
                        ) DEFAULT 'pending',
  rsvp_token          TEXT UNIQUE,            -- secure token for 1-click email RSVP without login
  invitation_sent_at  TIMESTAMPTZ NULL,
  reminder_sent_at    TIMESTAMPTZ NULL,
  created_at          TIMESTAMPTZ DEFAULT now()
);

-- push_subscriptions (stores Web Push API browser subscription endpoints)
CREATE TABLE push_subscriptions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL,
  endpoint    TEXT NOT NULL UNIQUE,
  p256dh      TEXT NOT NULL,
  auth        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- in_app_notifications
CREATE TABLE in_app_notifications (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL,
  event_id    UUID REFERENCES events(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  message     TEXT NOT NULL,
  is_read     BOOLEAN DEFAULT false,
  created_at  TIMESTAMPTZ DEFAULT now()
);
```

> [!NOTE]
> `meeting_id` is an opaque reference to the Meet service's DB. All display details (live call status, join link) are resolved via REST call or cached `meeting_link`.

---

## 5. Backend (FastAPI) — Structure & Endpoints

### 5.1 Folder Structure

```
calendar-backend/
  api/
    index.py                 # Vercel serverless entrypoint
  app/
    main.py
    config.py                # MEET_API_URL, INTERNAL_SERVICE_KEY, SMTP & VAPID settings
    db.py                    # async engine & session
    models.py                # SQLAlchemy 2.0 async models
    schemas.py               # Pydantic schemas
    auth/
      routes.py              # JWT verification (shared secret with Meet)
      deps.py
    events/
      routes.py              # user-facing CRUD for events & ICS download
      service.py
      recurrence.py          # RRULE expansion for date ranges
      ics.py                 # icalendar RFC 5545 generation
    invitations/
      routes.py              # RSVP handling (web & tokenized email links)
      service.py             # async email dispatch via aiosmtplib with attached .ics
    notifications/
      routes.py              # push subscription registration & in-app notifications
      service.py             # push notifications (pywebpush) & reminder scheduler
    internal/
      routes.py              # POST /internal/events (called BY Meet backend)
    meet_client.py           # httpx client calling Meet's /internal/meetings
  alembic/
  requirements.txt
  vercel.json
```

### 5.2 User-Facing Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/events?from=&to=` | List events in date range (expands recurring events) |
| `POST` | `/events` | Create event; if `add_video=true`, calls Meet's `/internal/meetings` first |
| `GET` | `/events/{id}` | Event details with attendee list and RSVP summary |
| `PATCH` | `/events/{id}` | Edit event (resends update emails if times change) |
| `DELETE` | `/events/{id}` | Delete event & cancel scheduled reminders |
| `GET` | `/events/{id}/ics` | **Download standard `.ics` calendar file** |
| `POST` | `/events/{id}/invite` | **Send or resend email invitations with `.ics` attachment** |
| `POST` | `/events/{id}/rsvp` | Logged-in attendee sets RSVP status (`yes`, `no`, `maybe`) |
| `POST` | `/rsvp/{token}` | **1-Click public RSVP from email invitation link** |
| `GET` | `/calendars` | List user's calendars |
| `POST` | `/calendars` | Create a new named calendar |
| `POST` | `/notifications/push-subscription` | **Register Web Push subscription (endpoint, p256dh, auth)** |
| `DELETE` | `/notifications/push-subscription` | Unregister Web Push subscription |
| `GET` | `/notifications` | List in-app notifications |
| `PATCH` | `/notifications/{id}/read` | Mark in-app notification as read |

### 5.3 Internal Endpoint (called by Meet backend)

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/internal/events` | Create calendar event from Meet-scheduled meeting. Body: `{ organizer_id, title, start_at, end_at, meeting_id, meeting_link }` |

```python
# app/internal/routes.py
@router.post("/internal/events")
async def create_event_from_meet(payload: InternalEventCreate, x_internal_api_key: str = Header(...)):
    if x_internal_api_key != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal service key")
    
    calendar_id = await get_or_create_default_calendar(payload.organizer_id)
    event = await create_event(
        calendar_id=calendar_id,
        organizer_id=payload.organizer_id,
        title=payload.title,
        start_at=payload.start_at,
        end_at=payload.end_at,
        meeting_id=payload.meeting_id,
        meeting_link=payload.meeting_link,
        source="meet",
    )
    return event
```

### 5.4 Calling Meet from Calendar (Video-Conferencing Toggle)

```python
# app/meet_client.py
import httpx
from datetime import datetime
from app.config import settings

async def create_meet_meeting(title: str, start_at: datetime) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.MEET_API_URL}/internal/meetings",
            json={"title": title, "scheduled_at": start_at.isoformat()},
            headers={"X-Internal-Api-Key": settings.INTERNAL_SERVICE_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()   # { "code": "abc-defg-hij", "join_url": "https://meet.../meet/abc-defg-hij" }
```

### 5.5 Corresponding addition on the **Meet backend**

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/internal/meetings` | Create scheduled meeting from Calendar. Same auth header check. Returns `{ code, join_url }`. |

### 5.6 ICS Generation, Email Invitations & Reminder Dispatch

#### A. Standard ICS File Builder (`app/events/ics.py`)
```python
from icalendar import Calendar, Event as ICSEvent, vCalAddress, vText, Alarm
from datetime import timedelta

def build_ics_content(event, attendees, organizer_email: str) -> bytes:
    cal = Calendar()
    cal.add('prodid', '-//Sidanex//Meridian Calendar//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'REQUEST')

    ie = ICSEvent()
    ie.add('uid', f"event-{event.id}@meridian.sidanex.com")
    ie.add('summary', event.title)
    if event.description:
        ie.add('description', event.description)
    if event.location:
        ie.add('location', event.location)
    if event.meeting_link:
        ie.add('url', event.meeting_link)

    ie.add('dtstart', event.start_at)
    ie.add('dtend', event.end_at)
    ie.add('status', 'CONFIRMED')

    # Organizer
    organizer = vCalAddress(f'MAILTO:{organizer_email}')
    organizer.params['cn'] = vText(organizer_email)
    ie.add('organizer', organizer)

    # Attendees
    for att in attendees:
        attendee = vCalAddress(f'MAILTO:{att.email}')
        attendee.params['cn'] = vText(att.email)
        attendee.params['partstat'] = vText(att.rsvp_status.upper())
        ie.add('attendee', attendee, encode=0)

    # Reminder Alarm
    if event.reminder_minutes_before:
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'Reminder: {event.title}')
        alarm.add('trigger', timedelta(minutes=-event.reminder_minutes_before))
        ie.add_component(alarm)

    cal.add_component(ie)
    return cal.to_ical()
```

#### B. Asynchronous Email Dispatch with `.ics` Attachment (`app/invitations/service.py`)
```python
import aiosmtplib
from email.message import EmailMessage
from app.config import settings

async def send_invitation_email(event, attendee, ics_bytes: bytes):
    if not settings.EMAIL_INVITES_ENABLED or not settings.SMTP_HOST:
        return

    msg = EmailMessage()
    msg['Subject'] = f"Invitation: {event.title} @ {event.start_at.strftime('%a %b %d, %Y %I:%M %p')}"
    msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg['To'] = attendee.email

    rsvp_yes_url = f"{settings.FRONTEND_URL}/rsvp/{attendee.rsvp_token}?status=yes"
    rsvp_no_url = f"{settings.FRONTEND_URL}/rsvp/{attendee.rsvp_token}?status=no"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
      <h2 style="color: #1a73e8; margin-top: 0;">{event.title}</h2>
      <p><strong>When:</strong> {event.start_at.strftime('%A, %B %d, %Y %I:%M %p')} - {event.end_at.strftime('%I:%M %p')}</p>
      {f'<p><strong>Video Call:</strong> <a href="{event.meeting_link}">{event.meeting_link}</a></p>' if event.meeting_link else ''}
      <p>{event.description or ''}</p>
      <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee;">
        <p style="font-weight: 600;">Going?</p>
        <a href="{rsvp_yes_url}" style="display: inline-block; padding: 8px 16px; background: #1a73e8; color: #fff; text-decoration: none; border-radius: 4px; margin-right: 8px;">Yes</a>
        <a href="{rsvp_no_url}" style="display: inline-block; padding: 8px 16px; background: #f1f3f4; color: #3c4043; text-decoration: none; border-radius: 4px;">No</a>
      </div>
    </div>
    """

    msg.set_content("Please find your calendar invitation attached.")
    msg.add_alternative(html_content, subtype='html')
    msg.add_attachment(ics_bytes, maintype='text', subtype='calendar', filename='invite.ics')

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
```

#### C. Browser Web Push Reminders (`app/notifications/service.py`)
```python
from pywebpush import webpush
import json
from app.config import settings

async def send_web_push_notification(subscription, title: str, body: str, event_url: str):
    if not settings.PUSH_NOTIFICATIONS_ENABLED or not settings.VAPID_PRIVATE_KEY:
        return

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": event_url,
        "icon": "/icon-192.png"
    })

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT}
        )
    except Exception as e:
        print(f"Push notification delivery failed: {e}")
```

---

## 6. Frontend (Vue 3) — Structure

```
calendar-frontend/
  src/
    views/
      MonthView.vue               # Monthly calendar grid with event chips
      WeekView.vue                # 7-day time slot grid
      DayView.vue                 # 24-hour detailed single day schedule
      PublicRsvpView.vue          # 1-click tokenized RSVP confirmation view
    components/
      EventCard.vue               # Color-coded event block with time & video badge
      EventDetailModal.vue        # Detail view with "Join Meet", RSVP list & "Download .ics"
      CreateEventModal.vue        # Event form + "Add video conferencing" toggle + attendees input
      MiniDatePicker.vue          # Sidebar mini month calendar
      CalendarSidebar.vue         # Sidebar with calendar toggles & reminder settings
      NotificationCenter.vue      # In-app notification list & browser push permission prompt
    stores/
      events.ts                   # Pinia store managing events, filters & recurrence
      notifications.ts            # Pinia store managing in-app toasts & push sub registration
    lib/
      api.ts                      # Axios/Fetch client with auth headers
      push.ts                     # Web Push service worker registration & VAPID key exchange
  public/
    sw.js                         # Service Worker handling push event & notificationclick
  vite.config.ts
  vercel.json
```

---

## 7. Shared Users / Single Sign-On (SSO)

Both apps use shared user accounts within the Sidanex ecosystem:
- Both backends point user verification at the same Neon Postgres `users` table.
- Both backends issue and verify JWT tokens signed with the identical `JWT_SECRET`.
- Logging in on either Meet or Calendar allows seamless single sign-on across both apps.

---

## 8. Environment Variables

### Calendar Backend (`calendar-backend/.env`)

```ini
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xyz.neon.tech/calendar_db
JWT_SECRET=your_shared_jwt_secret_same_as_meet
INTERNAL_SERVICE_KEY=your_shared_internal_service_key
MEET_API_URL=https://backend-omega-vert-20.vercel.app
FRONTEND_URL=https://meridian-calendar.vercel.app
CORS_ORIGINS=https://meridian-calendar.vercel.app,http://localhost:5173

# Email / SMTP Configuration (Free-tier SMTP like Resend/SendGrid/Gmail/Custom)
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=re_your_api_key
SMTP_FROM_EMAIL=calendar@sidanex.com
SMTP_FROM_NAME=Meridian Calendar

# Browser Web Push (VAPID Keys generated via web-push generate-vapid-keys)
VAPID_PUBLIC_KEY=BL...your_public_vapid_key
VAPID_PRIVATE_KEY=your_private_vapid_key
VAPID_SUBJECT=mailto:admin@sidanex.com

# Feature Flags
EMAIL_INVITES_ENABLED=true
EMAIL_REMINDERS_ENABLED=true
PUSH_NOTIFICATIONS_ENABLED=true
```

### Calendar Frontend (`calendar-frontend/.env`)

```ini
VITE_API_BASE_URL=https://your-calendar-backend.vercel.app
VITE_VAPID_PUBLIC_KEY=BL...your_public_vapid_key
VITE_MEET_APP_URL=https://frontend-seven-theta-86.vercel.app
```

### Additions to Meet Backend (`backend/.env`)

```ini
CALENDAR_API_URL=https://your-calendar-backend.vercel.app
INTERNAL_SERVICE_KEY=your_shared_internal_service_key
```

---

## 9. Local Development

- Start local Postgres for Calendar on a distinct port (e.g. `5433` or `5434`).
- Run Meet backend on port `:8000` and Calendar backend on port `:8001`.
- Set `MEET_API_URL=http://localhost:8000` on Calendar and `CALENDAR_API_URL=http://localhost:8001` on Meet for bidirectional integration testing.

---

## 10. Deployment (Vercel)

1. Deploy `meridian-frontend` and `meridian-backend` to Vercel.
2. Provision a dedicated Neon Postgres database for Calendar schema.
3. Configure identical `INTERNAL_SERVICE_KEY` and `JWT_SECRET` across both Vercel projects.
4. Set `MEET_API_URL` and `CALENDAR_API_URL` to each other's live Vercel domains.

---

## 11. Explicit Non-Goals

- **No two-way sync with third-party cloud calendars** (e.g. Google Calendar / Outlook OAuth account sync) — users import/export via universal standard `.ics` files instead.
- **No AI scheduling bots** (smart free/busy optimization, natural language conflict resolution) — focuses on clean, high-performance deterministic scheduling.