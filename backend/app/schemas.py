import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==========================================
# Auth Schemas
# ==========================================

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    display_name: str = Field(min_length=2, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    code: Optional[str] = None
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None


class SendOTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=4, max_length=10)
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==========================================
# Participant Schemas
# ==========================================

class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    guest_name: Optional[str] = None
    display_name: str
    role: str
    status: str
    joined_at: Optional[datetime] = None


# ==========================================
# Meeting Schemas
# ==========================================

class MeetingCreate(BaseModel):
    title: Optional[str] = "Instant Meeting"
    scheduled_at: Optional[datetime] = None
    lobby_enabled: bool = False  # default false for instant ease-of-use


class MeetingUpdateSettings(BaseModel):
    title: Optional[str] = None
    lobby_enabled: Optional[bool] = None
    is_locked: Optional[bool] = None


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: Optional[str] = None
    host_id: Optional[uuid.UUID] = None
    host_name: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    lobby_enabled: bool = False
    is_locked: bool = False
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    active_participants_count: int = 0


class MeetingJoinRequest(BaseModel):
    display_name: Optional[str] = None
    participant_id: Optional[uuid.UUID] = None


class MeetingJoinResponse(BaseModel):
    meeting: MeetingResponse
    participant_id: uuid.UUID
    role: str
    status: str
    livekit_token: Optional[str] = None
    livekit_url: str


class MeetingAdmitRequest(BaseModel):
    participant_id: uuid.UUID
    admit: bool = True  # True to admit, False to reject


# ==========================================
# LiveKit Token Schemas
# ==========================================

class LiveKitTokenRequest(BaseModel):
    display_name: str
    identity: Optional[str] = None
    is_host: bool = False


class LiveKitTokenResponse(BaseModel):
    token: str
    livekit_url: str
    room_name: str
    identity: str


# ==========================================
# Chat Schemas
# ==========================================

class ChatMessageCreate(BaseModel):
    sender_name: str
    sender_id: Optional[str] = None
    content: str = Field(min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    sender_name: str
    sender_id: Optional[str] = None
    content: str
    sent_at: datetime
