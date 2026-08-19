"""Redis-backed access-token blocklist and per-user revoke epoch."""

import logging
import time

from jose import JWTError
from redis.asyncio import Redis

from app.config import settings
from app.utils.jwt import decode_access_token

logger = logging.getLogger(__name__)

ACCESS_BLOCKLIST_PREFIX = "access_blocklist:"
ACCESS_REVOKE_BEFORE_PREFIX = "access_revoke_before:"


def _blocklist_key(jti: str) -> str:
    return f"{ACCESS_BLOCKLIST_PREFIX}{jti}"


def _revoke_before_key(user_id: str) -> str:
    return f"{ACCESS_REVOKE_BEFORE_PREFIX}{user_id}"


def access_check_keys(
    jti: str | None,
    user_id: str | None,
) -> tuple[str | None, str | None]:
    """Redis keys for blocklist + revoke-epoch checks in the auth hot path."""
    block_key = _blocklist_key(str(jti)) if jti else None
    revoke_key = _revoke_before_key(str(user_id)) if user_id else None
    return block_key, revoke_key


def parse_revoke_before(value: bytes | str | None, user_id: str) -> int | None:
    """Parse a Redis revoke-epoch value. None if missing or invalid."""
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode()
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("Invalid access revoke-before value for user=%s", user_id)
        return None


def _access_ttl_seconds() -> int:
    return max(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 1)


async def blocklist_access_token(redis: Redis, raw_token: str) -> bool:
    """
    Blocklist a single access token until it would have expired.
    Returns True if the token was blocklisted, False if it was unusable.
    """
    try:
        payload = decode_access_token(raw_token)
    except (JWTError, ValueError):
        return False

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or exp is None:
        return False

    ttl = int(exp) - int(time.time())
    if ttl <= 0:
        return False

    await redis.setex(_blocklist_key(str(jti)), ttl, "1")
    return True


async def is_access_token_blocklisted(redis: Redis, jti: str) -> bool:
    """Return True if this jti was revoked (logout / refresh rotation)."""
    return await redis.get(_blocklist_key(jti)) is not None


async def revoke_all_user_access_tokens(redis: Redis, user_id: str) -> None:
    """
    Invalidate every access token issued for this user before now.
    Kept for one access-token lifetime so old JWTs expire naturally.
    """
    now = int(time.time())
    await redis.setex(
        _revoke_before_key(user_id),
        _access_ttl_seconds(),
        str(now),
    )


async def get_access_revoke_before(redis: Redis, user_id: str) -> int | None:
    """Unix timestamp; reject access tokens with iat strictly before this."""
    value = await redis.get(_revoke_before_key(user_id))
    return parse_revoke_before(value, user_id)
