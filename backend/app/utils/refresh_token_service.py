import hashlib
import logging
import secrets

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

REFRESH_TOKEN_PREFIX = "refresh_token:"
USER_REFRESH_PREFIX = "user_refresh:"


def _make_key(token_hash: str) -> str:
    """Redis key for a refresh token hash."""
    return f"{REFRESH_TOKEN_PREFIX}{token_hash}"


def _user_tokens_key(user_id: str) -> str:
    """Redis set of refresh-token hashes for a user."""
    return f"{USER_REFRESH_PREFIX}{user_id}"


def _ttl_seconds() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def generate_refresh_token() -> str:
    """Cryptographically secure random token."""
    return secrets.token_hex(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash of the refresh token."""
    return hashlib.sha256(token.encode()).hexdigest()


def _decode_redis_value(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return value


async def store_refresh_token(redis: Redis, user_id: str) -> str:
    """
    Generate a refresh token, store its hash in Redis with TTL,
    and return the raw token to the client.
    """
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    key = _make_key(token_hash)
    ttl = _ttl_seconds()

    await redis.setex(key, ttl, user_id)
    user_key = _user_tokens_key(user_id)
    await redis.sadd(user_key, token_hash)
    await redis.expire(user_key, ttl)
    return raw_token


async def rotate_refresh_token(
    redis: Redis,
    raw_token: str,
) -> tuple[str, str] | None:
    """
    Validate and rotate a refresh token.

    Flow:
    1. Hash the incoming token
    2. Atomically get+delete the Redis key (rotation)
    3. Issue a new token for the same user
    4. Return (new_raw_token, user_id)

    Missing key → invalid, expired, or already used → None (401).
    """
    token_hash = hash_refresh_token(raw_token)
    key = _make_key(token_hash)

    user_id = await redis.getdel(key)
    if not user_id:
        logger.warning("Refresh token not found or already used")
        return None

    user_id = _decode_redis_value(user_id)
    await redis.srem(_user_tokens_key(user_id), token_hash)

    new_raw_token = await store_refresh_token(redis, user_id)
    return new_raw_token, user_id


async def revoke_refresh_token(redis: Redis, raw_token: str) -> bool:
    """
    Revoke a single refresh token (logout).
    Returns True if found and deleted, False if not found.
    """
    token_hash = hash_refresh_token(raw_token)
    key = _make_key(token_hash)

    user_id = await redis.getdel(key)
    if not user_id:
        return False

    user_id = _decode_redis_value(user_id)
    await redis.srem(_user_tokens_key(user_id), token_hash)
    return True


async def revoke_all_user_tokens(redis: Redis, user_id: str) -> None:
    """
    Revoke all refresh tokens for a user (logout-all / security events).
    """
    user_key = _user_tokens_key(user_id)
    hashes = await redis.smembers(user_key)
    for token_hash in hashes:
        token_hash = _decode_redis_value(token_hash)
        await redis.delete(_make_key(token_hash))
    await redis.delete(user_key)
