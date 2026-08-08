import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordUpdate, UserProfileUpdate, UserResponse
from app.utils.auth_cookies import clear_auth_cookies
from app.utils.auth_dependency import get_current_user
from app.utils.redis_client import get_redis
from app.utils.refresh_token_service import revoke_all_user_tokens
from app.utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

_REDIS_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Authentication service temporarily unavailable",
)


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get the current authenticated user's profile"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the current user's name or email"""
    updates = profile_update.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != current_user.email:
        existing_user = await db.execute(
            select(User).where(
                User.email == updates["email"],
                User.id != current_user.id,
            )
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    for key, value in updates.items():
        setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)

    logger.info(
        "User %s updated profile fields: %s",
        current_user.id,
        list(updates.keys()),
    )
    return current_user


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_update: PasswordUpdate,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Change the current user's password and revoke all sessions"""
    if not verify_password(
        password_update.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(password_update.new_password)

    try:
        await revoke_all_user_tokens(redis, str(current_user.id))
    except RedisError:
        logger.exception(
            "Redis unavailable while revoking sessions for user %s",
            current_user.id,
        )
        await db.rollback()
        raise _REDIS_UNAVAILABLE

    await db.commit()
    clear_auth_cookies(response)

    logger.info(
        "User %s changed password — all sessions revoked",
        current_user.id,
    )
