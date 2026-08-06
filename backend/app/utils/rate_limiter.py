import logging

from fastapi import HTTPException, Request, status
from jose import JWTError
from redis.asyncio import Redis

from app.utils.jwt import decode_access_token

logger = logging.getLogger(__name__)


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

    if current == 1:
        await redis.expire(key, window_seconds)

    if current > max_requests:
        logger.warning(
            "Rate limit exceeded key=%s count=%d limit=%d",
            key,
            current,
            max_requests,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {window_seconds} seconds.",
            headers={"Retry-After": str(window_seconds)},
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
    from app.utils.auth_cookies import ACCESS_COOKIE

    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
    else:
        token = request.cookies.get(ACCESS_COOKIE)

    if not token:
        return None

    try:
        payload = decode_access_token(token)
        return payload.get("sub")
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
    Uses user_id from JWT so corporate shared IPs
    don't affect other users on the same network.
    100 requests per minute per user.

    Falls back to IP if token is missing or invalid —
    unauthenticated requests to protected routes will
    fail auth anyway, this just adds a safety net.
    """
    user_id = get_user_id_from_request(request)

    if user_id:
        key = f"rate_limit:user:{user_id}"
    else:
        ip = get_client_ip(request)
        key = f"rate_limit:ip_fallback:{ip}"

    await check_rate_limit(redis, key, max_requests=100, window_seconds=60)
