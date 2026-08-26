import random
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

import aiosmtplib
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.config import settings
from app.db import get_db
from app.models import EmailOTP, User
from app.schemas import (
    GoogleAuthRequest,
    RefreshTokenRequest,
    SendOTPRequest,
    TokenResponse,
    UserLogin,
    UserResponse,
    UserSignup,
    VerifyOTPRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def send_otp_email(to_email: str, otp_code: str):
    """Sends OTP verification code using configured Gmail SMTP"""
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    message["To"] = to_email
    message["Subject"] = f"Your sidaz-meet Verification Code: {otp_code}"
    message.set_content(
        f"Hello,\n\nYour verification code for sidaz-meet is: {otp_code}\n\n"
        f"This code will expire in 10 minutes. If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nsidaz-meet Team"
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST or "smtp.gmail.com",
            port=settings.SMTP_PORT or 587,
            start_tls=True,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
        )
    except Exception as e:
        print(f"[sidaz-meet] SMTP Send Error: {e}")


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email.lower().strip())
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    new_user = User(
        email=user_data.email.lower().strip(),
        password_hash=get_password_hash(user_data.password),
        display_name=user_data.display_name.strip(),
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    access_token = create_access_token(user_id=new_user.id, email=new_user.email)
    refresh_token = create_refresh_token(user_id=new_user.id, email=new_user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Handles Google OAuth token exchange or ID token verification"""
    email = body.email
    display_name = body.display_name
    google_id = body.google_id
    avatar_url = body.avatar_url

    # If credential JWT token is passed, verify with Google token info
    if body.credential:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={body.credential}")
                if res.status_code == 200:
                    info = res.json()
                    email = info.get("email")
                    display_name = info.get("name") or display_name
                    google_id = info.get("sub")
                    avatar_url = info.get("picture") or avatar_url
        except Exception as e:
            print(f"[sidaz-meet] Google token verification error: {e}")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from Google authentication",
        )

    email_clean = email.lower().strip()
    stmt = select(User).where(User.email == email_clean)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Create user from Google Profile
        user = User(
            email=email_clean,
            display_name=display_name or email_clean.split("@")[0],
            google_id=google_id,
            avatar_url=avatar_url,
            password_hash=None,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    else:
        if google_id and not user.google_id:
            user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        await db.flush()

    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/otp/send")
async def send_otp(body: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    email_clean = body.email.lower().strip()
    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    otp_record = EmailOTP(
        email=email_clean,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(otp_record)
    await db.flush()

    await send_otp_email(email_clean, otp_code)

    return {"success": True, "message": "Verification code sent to your email"}


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(body: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    email_clean = body.email.lower().strip()
    now = datetime.now(timezone.utc)

    stmt = (
        select(EmailOTP)
        .where(
            EmailOTP.email == email_clean,
            EmailOTP.otp_code == body.otp_code.strip(),
            EmailOTP.is_used.is_(False),
            EmailOTP.expires_at > now,
        )
        .order_by(EmailOTP.created_at.desc())
    )
    result = await db.execute(stmt)
    otp_record = result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    otp_record.is_used = True
    await db.flush()

    # Find or create user
    user_stmt = select(User).where(User.email == email_clean)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        display_name = body.display_name or email_clean.split("@")[0]
        user = User(
            email=email_clean,
            display_name=display_name.strip(),
            password_hash=None,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=dict)
async def refresh_access_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token, expected_type="refresh")
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = uuid.UUID(user_id_str)
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    new_access_token = create_access_token(user_id=user.id, email=user.email)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
