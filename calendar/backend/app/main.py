from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.config import settings
from app.db import init_db
from app.events.routes import router as events_router
from app.internal.routes import router as internal_router
from app.invitations.routes import router as invitations_router
from app.notifications.routes import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        print(f"[meridian-calendar] Database init notice: {e}")
    yield


app = FastAPI(
    title="Meridian Calendar API",
    description="Backend service for Meridian Google Calendar clone with Meet integration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configuration
origins = settings.cors_origins_list
if "*" in origins:
    allow_origins = ["*"]
else:
    allow_origins = origins + [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(invitations_router)
app.include_router(notifications_router)
app.include_router(internal_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "app": "Meridian Calendar API",
        "status": "online",
        "meet_api_url": settings.MEET_API_URL,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
