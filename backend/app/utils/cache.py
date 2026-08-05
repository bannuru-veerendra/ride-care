import json
import logging
from typing import Any, TypeVar

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Cache TTLs in seconds
VEHICLE_CACHE_TTL = 60 * 5  # 5 minutes
NEXT_SERVICE_CACHE_TTL = 60 * 5  # 5 minutes
GUIDELINES_CACHE_TTL = 60 * 60 * 24  # 24 hours


# ── Key builders ──────────────────────────────────────────────

def vehicle_list_key(user_id: str) -> str:
    """Cache key for a user's vehicle list."""
    return f"cache:vehicles:user:{user_id}"


def vehicle_detail_key(vehicle_id: str) -> str:
    """Cache key for a single vehicle."""
    return f"cache:vehicle:{vehicle_id}"


def next_service_key(vehicle_id: str) -> str:
    """Cache key for next service info."""
    return f"cache:next_service:{vehicle_id}"


def vehicle_summary_key(vehicle_id: str) -> str:
    """Cache key for vehicle dashboard summary."""
    return f"cache:vehicle_summary:{vehicle_id}"


def vehicle_analytics_key(vehicle_id: str) -> str:
    """Cache key for vehicle analytics charts."""
    return f"cache:vehicle_analytics:{vehicle_id}"


def guidelines_key() -> str:
    """Cache key for maintenance guidelines."""
    return "cache:guidelines"


# ── Core get/set helpers ──────────────────────────────────────

async def cache_get(redis: Redis, key: str) -> Any | None:
    """
    Get a value from cache.
    Returns None on cache miss or Redis errors.
    Never raises — cache failures are non-fatal.
    """
    try:
        value = await redis.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        logger.warning("Cache GET failed key=%s error=%s", key, e)
        return None


async def cache_set(
    redis: Redis,
    key: str,
    value: Any,
    ttl: int,
) -> None:
    """
    Set a value in cache with TTL.
    Never raises — cache failures are non-fatal.
    """
    try:
        await redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning("Cache SET failed key=%s error=%s", key, e)


async def cache_delete(redis: Redis, *keys: str) -> None:
    """
    Delete one or more cache keys.
    Used for cache invalidation on write operations.
    Never raises.
    """
    try:
        if keys:
            await redis.delete(*keys)
            logger.debug("Cache invalidated keys=%s", keys)
    except Exception as e:
        logger.warning("Cache DELETE failed keys=%s error=%s", keys, e)


async def cache_delete_pattern(redis: Redis, pattern: str) -> None:
    """
    Delete all keys matching a pattern.
    Used for broad invalidation (e.g. all vehicle caches for a user).
    Uses SCAN to avoid blocking Redis.
    """
    try:
        async for key in redis.scan_iter(pattern):
            await redis.delete(key)
    except Exception as e:
        logger.warning(
            "Cache DELETE pattern failed pattern=%s error=%s", pattern, e
        )
