import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import get_current_user, get_optional_current_user
from app.config import settings
from app.db import get_db
from app.livekit_tokens.routes import mint_livekit_token
from app.meetings.service import (
    create_unique_meeting,
    get_active_participants_count,
    get_meeting_by_code,
    get_user_meeting_history,
    join_or_register_participant,
)
from app.models import Meeting, MeetingParticipant, User
from app.schemas import (
    MeetingAdmitRequest,
    MeetingCreate,
    MeetingJoinRequest,
    MeetingJoinResponse,
    MeetingResponse,
    MeetingUpdateSettings,
    ParticipantResponse,
)

router = APIRouter(tags=["meetings"])


def format_meeting_response(meeting: Meeting, active_count: int = 0) -> MeetingResponse:
    host_name = meeting.host.display_name if meeting.host else "Anonymous"
    return MeetingResponse(
        id=meeting.id,
        code=meeting.code,
        title=meeting.title,
        host_id=meeting.host_id,
        host_name=host_name,
        scheduled_at=meeting.scheduled_at,
        lobby_enabled=meeting.lobby_enabled,
        is_locked=meeting.is_locked,
        started_at=meeting.started_at,
        ended_at=meeting.ended_at,
        created_at=meeting.created_at,
        active_participants_count=active_count,
    )


async def sync_meeting_to_calendar(meeting: Meeting, host_id: Optional[uuid.UUID]):
    if not settings.CALENDAR_API_URL or not meeting.scheduled_at:
        return
    try:
        start_time = meeting.scheduled_at
        end_time = start_time + timedelta(minutes=45)
        join_url = f"{settings.FRONTEND_URL}/meet/{meeting.code}"
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.CALENDAR_API_URL}/internal/events",
                json={
                    "organizer_id": str(host_id) if host_id else None,
                    "title": meeting.title or "Scheduled Meeting",
                    "start_at": start_time.isoformat(),
                    "end_at": end_time.isoformat(),
                    "meeting_id": str(meeting.id),
                    "meeting_link": join_url,
                },
                headers={"X-Internal-Api-Key": settings.INTERNAL_SERVICE_KEY},
                timeout=5.0,
            )
    except Exception as e:
        print(f"[sidaz-meet] Calendar sync notice: {e}")


@router.post("/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_in: MeetingCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await create_unique_meeting(db, host=current_user, meeting_in=meeting_in)
    if meeting.scheduled_at:
        background_tasks.add_task(
            sync_meeting_to_calendar,
            meeting,
            current_user.id if current_user else None,
        )
    return format_meeting_response(meeting, active_count=1 if current_user else 0)


@router.get("/meetings/{code}", response_model=MeetingResponse)
async def get_meeting(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    active_count = await get_active_participants_count(db, meeting.id)
    return format_meeting_response(meeting, active_count=active_count)


@router.patch("/meetings/{code}/settings", response_model=MeetingResponse)
async def update_meeting_settings(
    code: str,
    settings_in: MeetingUpdateSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if meeting.host_id and meeting.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can modify meeting settings",
        )

    if settings_in.title is not None:
        meeting.title = settings_in.title
    if settings_in.lobby_enabled is not None:
        meeting.lobby_enabled = settings_in.lobby_enabled
    if settings_in.is_locked is not None:
        meeting.is_locked = settings_in.is_locked

    await db.flush()
    active_count = await get_active_participants_count(db, meeting.id)
    return format_meeting_response(meeting, active_count=active_count)


@router.post("/meetings/{code}/join", response_model=MeetingJoinResponse)
async def join_meeting(
    code: str,
    join_in: MeetingJoinRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if meeting.ended_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This meeting has already ended",
        )

    if meeting.is_locked:
        # If locked, only already admitted users or host can enter
        is_host = current_user and meeting.host_id and current_user.id == meeting.host_id
        if not is_host:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Meeting is locked by the host",
            )

    display_name = join_in.display_name
    if current_user:
        display_name = current_user.display_name
    elif not display_name or not display_name.strip():
        display_name = "Guest"
    display_name = display_name.strip()

    participant, needs_wait = await join_or_register_participant(
        db, meeting=meeting, user=current_user, guest_name=display_name, participant_id=join_in.participant_id
    )

    livekit_token = None
    if not needs_wait:
        is_host = participant.role in ("host", "co_host")
        identity = f"user_{current_user.id}" if current_user else f"guest_{participant.id}"
        livekit_token = mint_livekit_token(
            room_name=meeting.code,
            identity=identity,
            display_name=display_name,
            is_host=is_host,
        )

    active_count = await get_active_participants_count(db, meeting.id)
    return MeetingJoinResponse(
        meeting=format_meeting_response(meeting, active_count=active_count),
        participant_id=participant.id,
        role=participant.role,
        status=participant.status,
        livekit_token=livekit_token,
        livekit_url=settings.LIVEKIT_URL,
    )


@router.get("/meetings/{code}/participants", response_model=List[ParticipantResponse])
async def list_participants(
    code: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    stmt = (
        select(MeetingParticipant)
        .where(MeetingParticipant.meeting_id == meeting.id)
        .order_by(MeetingParticipant.joined_at.asc())
    )
    result = await db.execute(stmt)
    participants = result.scalars().all()

    response = []
    for p in participants:
        name = p.guest_name
        if p.user:
            name = p.user.display_name
        elif not name:
            name = "Participant"
        
        response.append(
            ParticipantResponse(
                id=p.id,
                meeting_id=p.meeting_id,
                user_id=p.user_id,
                guest_name=p.guest_name,
                display_name=name,
                role=p.role,
                status=p.status,
                joined_at=p.joined_at,
            )
        )
    return response


@router.post("/meetings/{code}/admit")
async def admit_participant(
    code: str,
    admit_in: MeetingAdmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if meeting.host_id and meeting.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can admit participants from the waiting lobby",
        )

    stmt = select(MeetingParticipant).where(
        MeetingParticipant.id == admit_in.participant_id,
        MeetingParticipant.meeting_id == meeting.id,
    )
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant request not found",
        )

    if admit_in.admit:
        participant.status = "admitted"
    else:
        participant.status = "rejected"
    await db.flush()

    return {"success": True, "participant_id": str(participant.id), "status": participant.status}


@router.post("/meetings/{code}/end")
async def end_meeting(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if meeting.host_id and meeting.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can end the meeting for all participants",
        )

    now = datetime.now(timezone.utc)
    meeting.ended_at = now
    await db.flush()

    return {"success": True, "ended_at": now.isoformat()}


@router.post("/meetings/{code}/leave")
async def leave_meeting(
    code: str,
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    stmt = select(MeetingParticipant).where(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting.id,
    )
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if participant:
        participant.left_at = datetime.now(timezone.utc)
        participant.status = "left"
        await db.flush()

    return {"success": True}


@router.post("/meetings/{code}/participants/{participant_id}/mute")
async def mute_participant(
    code: str,
    participant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    if meeting.host_id and meeting.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only host can mute participants",
        )
    return {"success": True, "action": "mute", "participant_id": str(participant_id)}


@router.post("/meetings/{code}/participants/{participant_id}/remove")
async def remove_participant(
    code: str,
    participant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    if meeting.host_id and meeting.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only host can remove participants",
        )

    stmt = select(MeetingParticipant).where(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting.id,
    )
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if participant:
        participant.status = "rejected"
        participant.left_at = datetime.now(timezone.utc)
        await db.flush()

    return {"success": True, "action": "remove", "participant_id": str(participant_id)}


@router.get("/users/me/meetings", response_model=List[MeetingResponse])
async def get_my_meetings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meetings = await get_user_meeting_history(db, current_user.id)
    return [format_meeting_response(m) for m in meetings]
