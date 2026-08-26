import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from livekit import api
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import get_optional_current_user
from app.config import settings
from app.db import get_db
from app.meetings.service import get_meeting_by_code
from app.models import User
from app.schemas import LiveKitTokenRequest, LiveKitTokenResponse

router = APIRouter(tags=["livekit"])


def mint_livekit_token(
    room_name: str,
    identity: str,
    display_name: str,
    is_host: bool = False,
) -> str:
    """Synchronous LiveKit AccessToken minting using API Key & Secret"""
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(display_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
                room_admin=is_host,
            )
        )
    )
    return token.to_jwt()


@router.post("/meetings/{code}/token", response_model=LiveKitTokenResponse)
async def get_livekit_token(
    code: str,
    request: LiveKitTokenRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting = await get_meeting_by_code(db, code)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if meeting.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This meeting has been locked by the host.",
        )

    is_host = False
    if current_user and meeting.host_id and current_user.id == meeting.host_id:
        is_host = True
    elif request.is_host:
        is_host = True

    identity = request.identity
    if not identity:
        if current_user:
            identity = f"user_{current_user.id}"
        else:
            identity = f"guest_{uuid.uuid4().hex[:8]}"

    display_name = request.display_name.strip()
    if not display_name and current_user:
        display_name = current_user.display_name
    elif not display_name:
        display_name = "Guest"

    token_jwt = mint_livekit_token(
        room_name=meeting.code,
        identity=identity,
        display_name=display_name,
        is_host=is_host,
    )

    return LiveKitTokenResponse(
        token=token_jwt,
        livekit_url=settings.LIVEKIT_URL,
        room_name=meeting.code,
        identity=identity,
    )
