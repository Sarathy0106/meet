# Meet Clone — Technical Build Specification

A digital twin of Google Meet, core features only (no AI features). This document is the
single source of truth for an AI coding agent (or a developer) to build the entire
application end to end.

---

## 1. High-Level Architecture

```
┌─────────────────────────┐        ┌──────────────────────────┐
│   Vue 3 SPA (Frontend)  │        │   FastAPI (Backend)      │
│   Deployed on Vercel    │◄──────►│   Deployed on Vercel     │
│   (Static + Vite build) │  REST  │   (Python serverless fn) │
└───────────┬─────────────┘        └────────────┬─────────────┘
            │                                    │
            │ WebRTC (audio/video/data)          │ SQL (asyncpg / SQLAlchemy)
            ▼                                    ▼
   ┌──────────────────────┐          ┌──────────────────────────┐
   │   LiveKit Cloud       │          │  Neon Postgres (prod)    │
   │   (managed SFU +      │          │  Local Postgres (dev)    │
   │   realtime signaling  │          └──────────────────────────┘
   │   + chat data channel)│
   └──────────────────────┘
```

### Why LiveKit Cloud (important — read before building)

Vercel functions (including our FastAPI backend) are **stateless, short-lived, request/response
only**. They cannot hold open WebSocket connections and cannot run a media server (SFU). Real
video calling needs exactly that: a persistent signaling channel and a server that forwards
audio/video packets between participants.

Instead of self-hosting that, we use **LiveKit Cloud** (free "Build" tier: 5,000 WebRTC
minutes/month, no credit card required) as a managed third-party service that provides:
- WebRTC signaling
- The SFU (media routing) — supports far more than 6 participants
- A built-in realtime **data channel** we reuse for in-call chat, raised hands, and
  presence/mute events — so we do **not** need a separate Pusher/Ably/WebSocket service.

Our FastAPI backend's only job regarding calls is to **mint short-lived LiveKit access tokens**
(a normal stateless REST call — fully Vercel-compatible) and to store business data (users,
meetings, chat history, participant records) in Postgres.

If LiveKit Cloud's free tier usage is ever exceeded, the same architecture works unchanged
against a self-hosted LiveKit server — only an environment variable changes.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Frontend framework | Vue 3 (Composition API) + Vite |
| Frontend state | Pinia |
| Frontend routing | Vue Router |
| Frontend styling | Tailwind CSS |
| Realtime media/SFU | LiveKit Cloud (`livekit-client` JS SDK) |
| Backend framework | FastAPI (Python 3.11+) |
| Backend server (local) | Uvicorn |
| Backend deploy target | Vercel Serverless Functions (Python runtime) |
| ORM | SQLAlchemy 2.0 (async) + Alembic for migrations |
| DB driver | `asyncpg` |
| Database (prod) | Neon Postgres (serverless Postgres) |
| Database (local) | Postgres 16 via Docker Compose |
| Auth | JWT (access + refresh tokens), `passlib[bcrypt]` for password hashing |
| Token/session library | `python-jose` (JWT) |
| Video/audio infra | LiveKit Cloud (server SDK `livekit-server-sdk` for token generation on backend) |
| Email link invites | Plain shareable meeting link (no email service required for MVP) |
| Frontend HTTP client | `axios` or native `fetch` |
| Hosting | Vercel (frontend project + backend project, both under one Vercel account) |

**Explicitly excluded (per requirements):** live captions, transcription, noise cancellation,
background blur/replacement, AI meeting notes, translation — all AI features are out of scope.

---

## 3. Core Feature List (Google Meet parity, no AI)

### 3.1 Auth & Users
- Sign up / log in with email + password (JWT-based)
- Persistent session (refresh token)
- Basic profile: display name, avatar (initials-based, no upload needed for MVP)
- Guest join (no account) via meeting link, entering a display name only

### 3.2 Meetings
- Create an instant meeting → generates a unique meeting code/link (e.g. `abc-defg-hij`)
- Schedule a future meeting (title, date/time, optional description) — stored in DB
- Join a meeting via code or link
- Host/co-host role vs participant role
- Waiting room / lobby: non-host participants wait for host approval before joining (host-created meetings only; instant meetings can skip lobby if creator enables "anyone can join")
- End meeting for all (host only) / leave meeting (any participant)
- Meeting history list ("Previous meetings") per user

### 3.3 In-Call Experience
- Video grid layout (auto-adjusting tile grid) and speaker (spotlight) view toggle
- Camera on/off toggle
- Microphone mute/unmute toggle
- Screen sharing (one participant at a time, or configurable multi-share)
- In-call text chat, scoped to the meeting session (sent via LiveKit data channel, persisted to DB)
- Participant list panel showing name, mute state, host badge
- Raise hand indicator
- Host controls: mute a participant, mute all, remove a participant, promote to co-host, lock meeting (block new joins), toggle lobby on/off
- Connection quality indicator per participant (from LiveKit connection stats)
- Device picker (select camera / microphone / speaker)
- Reconnect banner if a participant's connection drops and LiveKit auto-reconnects
- Pre-join screen: camera/mic preview + device selection before entering the call

### 3.4 Post-Call
- Meeting summary screen (duration, participant count) — no AI-generated notes
- Chat log remains viewable in meeting history

---

## 4. Data Model (Postgres)

```sql
-- users
users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- meetings
meetings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code          TEXT UNIQUE NOT NULL,        -- e.g. abc-defg-hij
  title         TEXT,
  host_id       UUID REFERENCES users(id),
  scheduled_at  TIMESTAMPTZ,                 -- null for instant meetings
  lobby_enabled BOOLEAN DEFAULT true,
  is_locked     BOOLEAN DEFAULT false,
  started_at    TIMESTAMPTZ,
  ended_at      TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- meeting_participants (also covers guests)
meeting_participants (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id    UUID REFERENCES meetings(id) ON DELETE CASCADE,
  user_id       UUID REFERENCES users(id) NULL,   -- null if guest
  guest_name    TEXT NULL,
  role          TEXT CHECK (role IN ('host','co_host','participant')) DEFAULT 'participant',
  joined_at     TIMESTAMPTZ,
  left_at       TIMESTAMPTZ
);

-- chat_messages
chat_messages (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id    UUID REFERENCES meetings(id) ON DELETE CASCADE,
  sender_name   TEXT NOT NULL,
  content       TEXT NOT NULL,
  sent_at       TIMESTAMPTZ DEFAULT now()
);
```

---

## 5. Backend (FastAPI) — Structure & Endpoints

### 5.1 Folder structure
```
backend/
  api/
    index.py            # Vercel entrypoint (imports app from main.py)
  app/
    main.py              # FastAPI app instance
    config.py             # env var settings (pydantic-settings)
    db.py                 # async engine/session
    models.py              # SQLAlchemy models
    schemas.py              # Pydantic request/response models
    auth/
      routes.py            # /auth/signup, /auth/login, /auth/refresh
      utils.py              # JWT + password hashing helpers
    meetings/
      routes.py            # create/join/schedule/end meeting endpoints
      service.py
    livekit_tokens/
      routes.py            # POST /meetings/{code}/token -> issues LiveKit access token
    chat/
      routes.py            # GET chat history for a meeting (persist-on-write from webhook or client POST)
  alembic/                  # migrations
  requirements.txt
  vercel.json
```

### 5.2 Key endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Returns access + refresh JWT |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/meetings` | Create instant or scheduled meeting |
| GET | `/meetings/{code}` | Get meeting metadata (title, host, lobby state) |
| POST | `/meetings/{code}/join` | Register participant (or guest), returns participant id |
| POST | `/meetings/{code}/token` | **Mint LiveKit access token** for the joining identity/room |
| POST | `/meetings/{code}/admit` | Host approves a waiting-room participant |
| POST | `/meetings/{code}/end` | Host ends meeting for all |
| POST | `/meetings/{code}/participants/{id}/mute` | Host mutes a participant |
| POST | `/meetings/{code}/participants/{id}/remove` | Host removes a participant |
| GET | `/meetings/{code}/chat` | Fetch persisted chat history |
| POST | `/meetings/{code}/chat` | Persist a chat message (called by client alongside sending over LiveKit data channel) |
| GET | `/users/me/meetings` | Meeting history for logged-in user |

### 5.3 LiveKit token endpoint (core of the whole system)
```python
from livekit import api

def create_token(room_name: str, identity: str, display_name: str, is_host: bool) -> str:
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(display_name) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            room_admin=is_host,
        ))
    return token.to_jwt()
```
This is a plain synchronous function — safe inside a Vercel serverless function, no
persistent connection required.

### 5.4 Vercel config for the Python backend (`backend/vercel.json`)
```json
{
  "builds": [{ "src": "api/index.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "api/index.py" }]
}
```
`api/index.py` simply does `from app.main import app` and re-exports it (Vercel's Python
runtime wraps the ASGI app automatically via `@vercel/python`'s ASGI support).

**Known limitation to design around:** cold starts and a max execution duration
(10s on Hobby, configurable higher on Pro) apply to every request — keep endpoints fast;
never attempt to hold a connection open in a backend route.

---

## 6. Frontend (Vue 3) — Structure

```
frontend/
  src/
    main.ts
    router/index.ts
    stores/
      auth.ts
      meeting.ts
    views/
      LoginView.vue
      SignupView.vue
      DashboardView.vue       # create/schedule/join, meeting history
      PreJoinView.vue          # camera/mic preview before entering
      MeetingRoomView.vue        # the actual call UI
      LobbyWaitingView.vue
    components/
      call/
        VideoTile.vue
        ParticipantGrid.vue
        ControlBar.vue          # mute/camera/screenshare/leave buttons
        ChatPanel.vue
        ParticipantListPanel.vue
        HostControlsMenu.vue
      common/
        AvatarInitials.vue
    lib/
      api.ts                    # axios instance -> backend base URL
      livekit.ts                 # wraps livekit-client Room connect/publish logic
  .env                          # VITE_API_BASE_URL, VITE_LIVEKIT_URL
  vite.config.ts
  vercel.json
```

### 6.1 Connecting to a call (client-side, in `MeetingRoomView.vue`)
```ts
import { Room, RoomEvent } from 'livekit-client'

const token = await api.post(`/meetings/${code}/token`, { display_name, is_host })
const room = new Room()
await room.connect(import.meta.env.VITE_LIVEKIT_URL, token.data.token)
await room.localParticipant.enableCameraAndMicrophone()

room.on(RoomEvent.DataReceived, (payload) => { /* chat / raise-hand messages */ })
room.on(RoomEvent.ParticipantConnected, updateGrid)
room.on(RoomEvent.ParticipantDisconnected, updateGrid)
```
Chat messages are sent via `room.localParticipant.publishData(...)` (LiveKit data channel)
AND posted to `/meetings/{code}/chat` so they're persisted for the meeting history view.

### 6.2 `frontend/vercel.json`
```json
{
  "buildCommand": "vite build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

## 7. Environment Variables

### Backend
```
DATABASE_URL=postgresql+asyncpg://...        # Neon in prod, local Postgres in dev
JWT_SECRET=
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LIVEKIT_URL=wss://your-project.livekit.cloud
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
```

### Frontend
```
VITE_API_BASE_URL=https://your-backend.vercel.app
VITE_LIVEKIT_URL=wss://your-project.livekit.cloud
```

---

## 8. Local Development

```
docker-compose.yml   # spins up local Postgres 16 on :5432
```
- Backend: `uvicorn app.main:app --reload` against local Postgres via `DATABASE_URL` pointed at Docker.
- Frontend: `npm run dev` (Vite) pointed at local backend via `VITE_API_BASE_URL=http://localhost:8000`.
- LiveKit: use the same LiveKit Cloud free-tier project for local dev too (no need to self-host
  LiveKit locally) — just point `LIVEKIT_URL`/`VITE_LIVEKIT_URL` at the cloud project from both
  local and prod environments.

---

## 9. Deployment (Vercel)

1. Two separate Vercel projects, same account: `meet-clone-frontend` and `meet-clone-backend`, both connected to their respective folders in the repo (or two repos).
2. Set the environment variables above in each project's Vercel dashboard (per environment: Preview/Production).
3. Neon: create a Postgres project, run Alembic migrations against the Neon connection string once (`alembic upgrade head`) before first deploy.
4. LiveKit Cloud: create a free project at livekit.io, copy API key/secret/URL into backend env vars, copy the WS URL into frontend env vars.
5. Set `CORS_ORIGINS` on the backend to the deployed frontend's Vercel URL.

---

## 10. Explicit Non-Goals

- No AI noise cancellation, live captions, transcription, or meeting summaries
- No recording-to-cloud-storage pipeline (can be added later; out of scope for MVP)
- No mobile native apps (responsive web only)
- No calendar (Google/Outlook) integration — scheduling is internal only