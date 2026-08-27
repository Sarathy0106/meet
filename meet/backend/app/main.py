from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.config import settings
from app.db import init_db
from app.internal.routes import router as internal_router
from app.livekit_tokens.routes import router as livekit_router
from app.meetings.routes import router as meetings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize tables on startup (works seamlessly with Postgres or SQLite dev fallback)
    try:
        await init_db()
    except Exception as e:
        print(f"[sidaz-meet] Database initialization note: {e}")
    yield


app = FastAPI(
    title="sidaz-meet API",
    description="Backend API for Google Meet digital twin clone",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-seven-theta-86.vercel.app",
        "https://meridian-calendar-frontend.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(meetings_router)
app.include_router(livekit_router)
app.include_router(chat_router)
app.include_router(internal_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "app": "sidaz-meet API",
        "status": "online",
        "livekit_url": settings.LIVEKIT_URL,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
