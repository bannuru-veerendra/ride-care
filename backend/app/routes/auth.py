import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SessionResponse,
    TokenResponse,
    UserCreate,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse
from app.utils.access_token_service import (
    blocklist_access_token,
    revoke_all_user_access_tokens,
)
from app.utils.auth_cookies import (
    access_token_from_request,
    clear_auth_cookies,
    refresh_token_from_request,
    set_auth_cookies,
)
from app.utils.auth_session import REDIS_UNAVAILABLE, authenticate_user
from app.utils.cache import cache_delete, user_identity_key
from app.utils.email_verification_service import (
    consume_verification_token,
    issue_verification_email,
)
from app.utils.jwt import create_access_token
from app.utils.password_reset_service import (
    consume_reset_token,
    issue_password_reset_email,
)
from app.utils.rate_limiter import auth_rate_limit
from app.utils.redis_client import get_redis
from app.utils.refresh_token_service import (
    revoke_all_user_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UserResponse:
    """Register a new user and send an email verification link."""
    await auth_rate_limit(request, redis)

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
        email_verified=False,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    try:
        await issue_verification_email(
            redis,
            user_id=str(db_user.id),
            email=db_user.email,
            full_name=db_user.full_name,
        )
    except RedisError:
        logger.exception("Redis unavailable while storing verification token")
        raise REDIS_UNAVAILABLE
    return db_user


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Consume a verification token and mark the user's email as verified."""
    await auth_rate_limit(request, redis)

    try:
        user_id = await consume_verification_token(redis, body.token)
    except RedisError:
        logger.exception("Redis unavailable during email verification")
        raise REDIS_UNAVAILABLE

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link",
        )

    if not db_user.email_verified:
        db_user.email_verified = True
        await db.commit()

    return MessageResponse(message="Email verified. You can sign in now.")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """
    Resend verification email.
    Always returns the same message to avoid email enumeration.
    """
    await auth_rate_limit(request, redis)

    result = await db.execute(select(User).where(User.email == body.email))
    db_user = result.scalar_one_or_none()
    if (
        db_user is not None
        and db_user.is_active
        and not db_user.email_verified
    ):
        try:
            await issue_verification_email(
                redis,
                user_id=str(db_user.id),
                email=db_user.email,
                full_name=db_user.full_name,
            )
        except RedisError:
            logger.exception("Redis unavailable while storing verification token")
            raise REDIS_UNAVAILABLE

    return MessageResponse(
        message="If that email is registered and unverified, a new link has been sent.",
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """
    Request a password reset email.
    Always returns the same message to avoid email enumeration.
    """
    await auth_rate_limit(request, redis)

    result = await db.execute(select(User).where(User.email == body.email))
    db_user = result.scalar_one_or_none()
    if db_user is not None and db_user.is_active:
        try:
            await issue_password_reset_email(
                redis,
                user_id=str(db_user.id),
                email=db_user.email,
                full_name=db_user.full_name,
            )
        except RedisError:
            logger.exception("Redis unavailable while storing password reset token")
            raise REDIS_UNAVAILABLE

    return MessageResponse(
        message="If that email is registered, a password reset link has been sent.",
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Consume a reset token, set a new password, and revoke all sessions."""
    await auth_rate_limit(request, redis)

    try:
        user_id = await consume_reset_token(redis, body.token)
    except RedisError:
        logger.exception("Redis unavailable during password reset")
        raise REDIS_UNAVAILABLE

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link",
        )

    db_user.hashed_password = hash_password(body.new_password)

    try:
        await revoke_all_user_tokens(redis, str(db_user.id))
        await revoke_all_user_access_tokens(redis, str(db_user.id))
        await cache_delete(redis, user_identity_key(str(db_user.id)))
    except RedisError:
        logger.exception(
            "Redis unavailable while revoking sessions after password reset for user %s",
            db_user.id,
        )
        await db.rollback()
        raise REDIS_UNAVAILABLE

    await db.commit()
    logger.info("User %s reset password via email link", db_user.id)
    return MessageResponse(
        message="Password updated. You can sign in with your new password.",
    )


@router.post("/login", response_model=SessionResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SessionResponse:
    """Login with JSON body (`email` + `password`). Sets httpOnly auth cookies."""
    await auth_rate_limit(request, redis)
    tokens = await authenticate_user(
        credentials.email, credentials.password, db, redis
    )
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return SessionResponse()


@router.post("/token", response_model=TokenResponse)
async def token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    """OAuth2 token endpoint for Swagger Authorize (`username` = email)."""
    await auth_rate_limit(request, redis)
    tokens = await authenticate_user(
        form_data.username, form_data.password, db, redis
    )
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


@router.post("/refresh", response_model=SessionResponse)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest = RefreshRequest(),
    redis: Redis = Depends(get_redis),
) -> SessionResponse:
    """Rotate refresh token and issue a new access token. Reads cookie if body omits token."""
    refresh_token = refresh_token_from_request(request, body.refresh_token)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    try:
        result = await rotate_refresh_token(redis, refresh_token)
    except RedisError:
        logger.exception("Redis unavailable during refresh")
        raise REDIS_UNAVAILABLE

    if result is None:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_refresh_token, user_id = result

    # Prefer to kill the previous access JWT immediately; if Redis blips here the
    # refresh already rotated — still issue new cookies (old access dies by TTL).
    old_access = access_token_from_request(request)
    if old_access:
        try:
            await blocklist_access_token(redis, old_access)
        except RedisError:
            logger.exception(
                "Redis unavailable while blocklisting access token on refresh"
            )

    access_token = create_access_token(user_id)
    set_auth_cookies(response, access_token, new_refresh_token)
    return SessionResponse()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    body: LogoutRequest = LogoutRequest(),
    redis: Redis = Depends(get_redis),
) -> Response:
    """Revoke refresh + blocklist access token, then clear auth cookies."""
    refresh_token = refresh_token_from_request(request, body.refresh_token)
    access_token = access_token_from_request(request)
    try:
        if refresh_token:
            await revoke_refresh_token(redis, refresh_token)
        if access_token:
            await blocklist_access_token(redis, access_token)
    except RedisError:
        logger.exception("Redis unavailable during logout")
        raise REDIS_UNAVAILABLE
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
