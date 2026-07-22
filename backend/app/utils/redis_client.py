from redis.asyncio import Redis, from_url

from app.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    """
    Returns the Redis client singleton.
    Uses Upstash REDIS_URL with TLS (rediss://).
    """
    global _redis
    if _redis is None:
        _redis = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,
        )
    return _redis


async def close_redis() -> None:
    """Close the Redis connection on app shutdown."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
