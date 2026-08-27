import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.utils import create_access_token, get_password_hash, verify_password
from app.db import get_db
from app.events.service import get_or_create_default_calendar
from app.models import User
from app.schemas import GuestLogin, TokenResponse, UserLogin, UserResponse, UserSignup

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/guest", response_model=TokenResponse)
async def guest_auth(
    payload: GuestLogin = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates or provisions a session for a guest or initial user.
    """
    email = (payload.email if payload and payload.email else f"guest_{str(uuid.uuid4())[:8]}@meridian.local").lower()
    display_name = (payload.display_name if payload and payload.display_name else email.split("@")[0].capitalize())

    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            display_name=display_name,
        )
        db.add(user)
        await db.flush()

    # Ensure default calendar exists
    await get_or_create_default_calendar(db, user.id)

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserSignup,
    db: AsyncSession = Depends(get_db),
):
    email = payload.email.lower().strip()
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()

    await get_or_create_default_calendar(db, user.id)

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    email = payload.email.lower().strip()
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    await get_or_create_default_calendar(db, user.id)

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }
