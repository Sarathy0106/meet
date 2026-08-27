import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Base Config
class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# User Schema
class UserResponse(OrmBase):
    id: uuid.UUID
    email: str
    display_name: str
    avatar_url: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class GuestLogin(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Calendar Schemas
class CalendarCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = "#4285F4"


class CalendarResponse(OrmBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    color: str
    is_default: bool
    created_at: datetime


# Attendee Schemas
class AttendeeCreate(BaseModel):
    email: EmailStr
    user_id: Optional[uuid.UUID] = None
    attendee_type: str = "external"


class AttendeeResponse(OrmBase):
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    email: str
    attendee_type: str
    rsvp_status: str
    invitation_sent_at: Optional[datetime] = None
    reminder_sent_at: Optional[datetime] = None


class RSVPRequest(BaseModel):
    status: str = Field(..., pattern="^(yes|no|maybe)$")


# Event Schemas
class EventCreate(BaseModel):
    calendar_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    recurrence_rule: Optional[str] = None
    reminder_minutes_before: Optional[int] = 10
    color: Optional[str] = None
    add_video: bool = False  # If True, requests Meet to create a meeting
    attendees: Optional[List[AttendeeCreate]] = None


class EventUpdate(BaseModel):
    calendar_id: Optional[uuid.UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    all_day: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    reminder_minutes_before: Optional[int] = None
    color: Optional[str] = None
    meeting_link: Optional[str] = None
    attendees: Optional[List[AttendeeCreate]] = None


class EventResponse(OrmBase):
    id: uuid.UUID
    calendar_id: uuid.UUID
    organizer_id: uuid.UUID
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: datetime
    end_at: datetime
    all_day: bool
    recurrence_rule: Optional[str] = None
    reminder_minutes_before: Optional[int] = 10
    meeting_id: Optional[uuid.UUID] = None
    meeting_link: Optional[str] = None
    source: str
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    attendees: List[AttendeeResponse] = []


# Internal Event Creation from Meet
class InternalEventCreate(BaseModel):
    organizer_id: Optional[uuid.UUID] = None
    title: str
    start_at: datetime
    end_at: datetime
    meeting_id: Optional[uuid.UUID] = None
    meeting_link: Optional[str] = None
    description: Optional[str] = None


# Push Subscription Schema
class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


# In-App Notification Schema
class InAppNotificationResponse(OrmBase):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: Optional[uuid.UUID] = None
    title: str
    message: str
    is_read: bool
    created_at: datetime
