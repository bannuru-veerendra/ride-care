import logging

from fastapi import HTTPException, Request, status
from jose import JWTError
from redis.asyncio import Redis

from app.utils.access_token_service import access_check_keys, parse_revoke_before
from app.utils.auth_context import (
    AuthHotPath,
    get_access_token_from_request,
    set_auth_hot_path,
)
from app.utils.cache import parse_user_identity, user_identity_key
from app.utils.jwt import decode_access_token

logger = logging.getLogger(__name__)

USER_RATE_MAX = 100
USER_RATE_WINDOW_SECONDS = 60


async def _enforce_rate_limit(
    redis: Redis,
    key: str,
    count: int,
    max_requests: int,
    window_seconds: int,
) -> None:
    """Apply EXPIRE on first hit and raise 429 when the window is exceeded."""
    if count == 1:
        await redis.expire(key, window_seconds)

    if count > max_requests:
        logger.warning(
            "Rate limit exceeded key=%s count=%d limit=%d",
            key,
            count,
            max_requests,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {window_seconds} seconds.",
            headers={"Retry-After": str(window_seconds)},
        )


async def check_rate_limit(
    redis: Redis,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """
    Sliding window rate limiter using Redis INCR + EXPIRE.

    Flow:
    1. Increment counter for this key
    2. On first request, set TTL for the window
    3. If counter exceeds limit, raise 429

    Key is scoped by identity + endpoint so limits are
    independent per user/IP and route.
    """
    current = await redis.incr(key)
    await _enforce_rate_limit(
        redis, key, current, max_requests, window_seconds
    )


def get_client_ip(request: Request) -> str:
    """
    Extract real client IP.
    Checks X-Forwarded-For first (set by Render proxy),
    falls back to direct connection IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_id_from_request(request: Request) -> str | None:
    """
    Extract user_id from JWT in the Authorization header or access cookie
    without going through the full FastAPI dependency chain.
    Returns None if token is missing or invalid.
    """
    token = get_access_token_from_request(request)
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except (JWTError, ValueError, Exception):
        return None


def _decode_payload(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        return decode_access_token(token)
    except (JWTError, ValueError, Exception):
        return None


async def auth_rate_limit(request: Request, redis: Redis) -> None:
    """
    Rate limit for unauthenticated auth endpoints.
    Uses IP since no user identity is available yet.
    10 requests per minute per IP — lenient enough for
    shared office/university networks.
    """
    ip = get_client_ip(request)
    endpoint = request.url.path.replace("/", "_")
    key = f"rate_limit:auth:{ip}:{endpoint}"
    await check_rate_limit(redis, key, max_requests=10, window_seconds=60)


async def user_rate_limit(request: Request, redis: Redis) -> None:
    """
    Rate limit for authenticated API endpoints.

    One Redis round-trip: INCR the limiter plus GET blocklist,
    revoke-epoch, and user identity so get_current_user does not
    pay extra Upstash RTTs on the same request.
    """
    token = get_access_token_from_request(request)
    payload = _decode_payload(token)
    user_id = payload.get("sub") if payload else None
    jti = payload.get("jti") if payload else None

    if user_id:
        rate_key = f"rate_limit:user:{user_id}"
    else:
        rate_key = f"rate_limit:ip_fallback:{get_client_ip(request)}"

    block_key, revoke_key = access_check_keys(jti, user_id)
    identity_key = user_identity_key(str(user_id)) if user_id else None

    pipe = redis.pipeline(transaction=False)
    pipe.incr(rate_key)
    if block_key:
        pipe.get(block_key)
    if revoke_key:
        pipe.get(revoke_key)
    if identity_key:
        pipe.get(identity_key)
    results = await pipe.execute()

    count = int(results[0])
    idx = 1
    blocked_raw = None
    revoke_raw = None
    identity_raw = None
    if block_key:
        blocked_raw = results[idx]
        idx += 1
    if revoke_key:
        revoke_raw = results[idx]
        idx += 1
    if identity_key:
        identity_raw = results[idx]

    await _enforce_rate_limit(
        redis,
        rate_key,
        count,
        USER_RATE_MAX,
        USER_RATE_WINDOW_SECONDS,
    )

    set_auth_hot_path(
        request,
        AuthHotPath(
            payload=payload,
            blocklisted=blocked_raw is not None,
            revoke_before=parse_revoke_before(
                revoke_raw, str(user_id) if user_id else ""
            ),
            cached_user=parse_user_identity(identity_raw),
        ),
    )
