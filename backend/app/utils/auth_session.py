"""Login credential checks and access/refresh token issuance."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.jwt import create_access_token
from app.utils.refresh_token_service import store_refresh_token
from app.utils.security import normalize_email, verify_password

logger = logging.getLogger(__name__)

REDIS_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Authentication service temporarily unavailable",
)

EMAIL_NOT_VERIFIED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Email not verified. Check your inbox or request a new verification link.",
)


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str


async def authenticate_user(
    email: str,
    password: str,
    db: AsyncSession,
    redis: Redis,
) -> IssuedTokens:
    """Validate credentials and issue access + refresh tokens."""
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

    if not db_user.email_verified:
        logger.warning("Login failed: email not verified for email=%s", email)
        raise EMAIL_NOT_VERIFIED

    user_id = str(db_user.id)
    access_token = create_access_token(user_id)
    try:
        refresh_token = await store_refresh_token(redis, user_id)
    except RedisError:
        logger.exception("Redis unavailable while issuing refresh token")
        raise REDIS_UNAVAILABLE

    return IssuedTokens(access_token=access_token, refresh_token=refresh_token)
