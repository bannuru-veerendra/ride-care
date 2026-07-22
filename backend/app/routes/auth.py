import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    normalize_email,
)
from app.utils.jwt import create_access_token
from app.utils.redis_client import get_redis
from app.utils.refresh_token_service import (
    revoke_refresh_token,
    rotate_refresh_token,
    store_refresh_token,
)
from app.utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _authenticate_user(
    email: str,
    password: str,
    db: AsyncSession,
    redis: Redis,
) -> TokenResponse:
    """Validate credentials and return access + refresh tokens."""
    email = normalize_email(email)
    result = await db.execute(select(User).where(User.email == email))
    db_user = result.scalar_one_or_none()

    if not db_user:
        logger.warning("Login failed: no user found for email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not db_user.is_active:
        logger.warning("Login failed: inactive account for email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(password, db_user.hashed_password):
        logger.warning("Login failed: wrong password for email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user_id = str(db_user.id)
    access_token = create_access_token(user_id)
    refresh_token = await store_refresh_token(redis, user_id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """Register a new user"""
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hash_password(user.password),
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    """Login with JSON body (`email` + `password`)."""
    return await _authenticate_user(
        credentials.email, credentials.password, db, redis
    )


@router.post("/token", response_model=TokenResponse)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    """OAuth2 token endpoint for Swagger Authorize (`username` = email)."""
    return await _authenticate_user(
        form_data.username, form_data.password, db, redis
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    """Rotate refresh token and issue a new access token."""
    result = await rotate_refresh_token(redis, body.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_refresh_token, user_id = result
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    redis: Redis = Depends(get_redis),
) -> Response:
    """Revoke the given refresh token."""
    await revoke_refresh_token(redis, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
