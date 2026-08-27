# sidaz-meet — Google Meet Digital Twin

A high-performance, digital twin of **Google Meet** built with **FastAPI** (stateless Python backend with LiveKit access token minting and PostgreSQL persistence) and **Vue 3 + Vite + Tailwind CSS** (WebRTC SFU audio/video, in-call chat, and host controls via LiveKit Cloud).

---

## Architecture Overview

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

---

## Features

- **Authentication & Profiles**:
  - JWT Access & Refresh token system with automatic silent renewal.
  - Sign up, Login, and Guest join with display name.
- **Meetings**:
  - Instant meeting creation with Google Meet code format (`xxx-yyyy-zzz`).
  - Scheduled meetings with date/time and waiting lobby toggles.
  - Host vs Participant roles and meeting lock controls.
  - Waiting Lobby with Host Knock approvals (`Admit` / `Deny` / `Admit All`).
  - Meeting history with persistent chat log review.
- **In-Call Experience**:
  - Auto-adjusting dynamic grid and Spotlight / Screen-share presentation mode.
  - Camera on/off, Mic mute/unmute, and Screen sharing.
  - Realtime in-call text chat (LiveKit data channel + database persistence).
  - Raise hand indicator with animated visual cues.
  - Host moderation (remote mute, kick participant, end meeting for all).
  - Audio/Video device selection with live preview and audio test tone.
  - Auto-reconnect banner for network drop handling.
  - Pre-join preview screen.

---

## Quick Start (Local Development)

### 1. Database (Local Postgres via Docker)
```bash
docker compose up -d
```
*Note: If Docker is not running, the backend automatically falls back to local SQLite for seamless zero-config testing.*

### 2. Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations (or let FastAPI auto-initialize on startup)
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```
API docs available at: `http://localhost:8000/docs`

### 3. Frontend (Vue 3 + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## LiveKit Cloud Configuration

1. Create a free account at [livekit.io](https://livekit.io) (Free "Build" tier: 5,000 WebRTC minutes/month, no credit card required).
2. Create a project and copy your **WebSocket URL**, **API Key**, and **API Secret**.
3. Set environment variables:
   - **Backend (`backend/.env`)**:
     ```env
     LIVEKIT_API_KEY=your_livekit_key
     LIVEKIT_API_SECRET=your_livekit_secret
     LIVEKIT_URL=wss://your-project.livekit.cloud
     ```
   - **Frontend (`frontend/.env`)**:
     ```env
     VITE_LIVEKIT_URL=wss://your-project.livekit.cloud
     VITE_API_BASE_URL=http://localhost:8000
     ```

---

## Production Deployment (Vercel + Neon)

### 1. Neon Postgres
1. Create a serverless PostgreSQL database at [neon.tech](https://neon.tech).
2. Copy the connection string into `DATABASE_URL` (format: `postgresql+asyncpg://...`).

### 2. Backend Deployment (Vercel)
- Deploy `backend/` directory to Vercel as a Python Serverless Function.
- Set environment variables in the Vercel Dashboard:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `LIVEKIT_API_KEY`
  - `LIVEKIT_API_SECRET`
  - `LIVEKIT_URL`
  - `CORS_ORIGINS` (pointing to your frontend Vercel URL)

### 3. Frontend Deployment (Vercel)
- Deploy `frontend/` directory to Vercel as a Vite SPA.
- Set environment variables in the Vercel Dashboard:
  - `VITE_API_BASE_URL` (pointing to your deployed backend URL)
  - `VITE_LIVEKIT_URL` (LiveKit Cloud WebSocket URL)

---

## Testing

Run the automated backend test suite:
```bash
cd backend
PYTHONPATH=. venv/bin/pytest -c pytest.ini tests/test_api.py -v
```

Test the production frontend build:
```bash
cd frontend
npm run build
```
