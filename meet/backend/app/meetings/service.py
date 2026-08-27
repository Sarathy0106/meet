import random
import string
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Meeting, MeetingParticipant, User
from app.schemas import MeetingCreate, MeetingUpdateSettings


def generate_meeting_code() -> str:
    """Generates a Google Meet style code: xxx-yyyy-zzz (lowercase letters)"""
    part1 = "".join(random.choices(string.ascii_lowercase, k=3))
    part2 = "".join(random.choices(string.ascii_lowercase, k=4))
    part3 = "".join(random.choices(string.ascii_lowercase, k=3))
    return f"{part1}-{part2}-{part3}"


async def create_unique_meeting(
    db: AsyncSession,
    host: Optional[User],
    meeting_in: MeetingCreate
) -> Meeting:
    for _ in range(10):
        code = generate_meeting_code()
        stmt = select(Meeting).where(Meeting.code == code)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            break
    else:
        # Fallback with uuid suffix if conflict loop
        code = f"meet-{uuid.uuid4().hex[:8]}"

    now = datetime.now(timezone.utc)
    meeting = Meeting(
        code=code,
        title=meeting_in.title or ("Instant Meeting" if not meeting_in.scheduled_at else "Scheduled Meeting"),
        host_id=host.id if host else None,
        scheduled_at=meeting_in.scheduled_at,
        lobby_enabled=meeting_in.lobby_enabled,
        is_locked=False,
        started_at=now if not meeting_in.scheduled_at else None,
        created_at=now,
    )
    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)

    # If host exists, register host as first participant
    if host:
        host_participant = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=host.id,
            role="host",
            status="admitted",
            joined_at=now,
        )
        db.add(host_participant)
        await db.flush()

    return meeting


async def get_meeting_by_code(
    db: AsyncSession,
    code: str
) -> Optional[Meeting]:
    # Normalize code (strip whitespace and lower)
    clean_code = code.strip().lower()
    stmt = (
        select(Meeting)
        .where(Meeting.code == clean_code)
        .options(selectinload(Meeting.host), selectinload(Meeting.participants))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_active_participants_count(
    db: AsyncSession,
    meeting_id: uuid.UUID
) -> int:
    stmt = (
        select(func.count(MeetingParticipant.id))
        .where(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.status == "admitted",
            MeetingParticipant.left_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def join_or_register_participant(
    db: AsyncSession,
    meeting: Meeting,
    user: Optional[User],
    guest_name: Optional[str],
    participant_id: Optional[uuid.UUID] = None,
) -> Tuple[MeetingParticipant, bool]:
    """
    Registers a participant for a meeting.
    Returns (participant, needs_lobby_wait).
    """
    now = datetime.now(timezone.utc)
    is_host = user is not None and meeting.host_id is not None and user.id == meeting.host_id

    existing_participant = None
    if participant_id:
        stmt = (
            select(MeetingParticipant)
            .where(
                MeetingParticipant.id == participant_id,
                MeetingParticipant.meeting_id == meeting.id,
            )
        )
        result = await db.execute(stmt)
        existing_participant = result.scalar_one_or_none()

    if not existing_participant and user:
        stmt = (
            select(MeetingParticipant)
            .where(
                MeetingParticipant.meeting_id == meeting.id,
                MeetingParticipant.user_id == user.id,
            )
        )
        result = await db.execute(stmt)
        existing_participant = result.scalar_one_or_none()

    if existing_participant:
        # Rejoining
        if is_host:
            existing_participant.role = "host"
            existing_participant.status = "admitted"
        elif existing_participant.status == "left":
            existing_participant.status = "waiting" if meeting.lobby_enabled else "admitted"
        existing_participant.left_at = None
        await db.flush()
        needs_wait = (existing_participant.status == "waiting")
        return existing_participant, needs_wait

    # Create new participant
    role = "host" if is_host else "participant"
    status = "admitted"
    if meeting.lobby_enabled and not is_host:
        status = "waiting"

    new_participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=user.id if user else None,
        guest_name=guest_name if not user else None,
        role=role,
        status=status,
        joined_at=now,
    )
    db.add(new_participant)
    await db.flush()
    await db.refresh(new_participant)

    needs_wait = (status == "waiting")
    return new_participant, needs_wait


async def get_user_meeting_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20
) -> List[Meeting]:
    stmt = (
        select(Meeting)
        .distinct()
        .outerjoin(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)
        .where(
            (Meeting.host_id == user_id) | (MeetingParticipant.user_id == user_id)
        )
        .order_by(Meeting.created_at.desc())
        .limit(limit)
        .options(selectinload(Meeting.host))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
