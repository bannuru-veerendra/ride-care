"""Access JWT helpers with jti / iat claims."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt import PyJWTError as JWTError

from app.config import settings

ALGORITHM = "HS256"

__all__ = ["JWTError", "create_access_token", "decode_access_token"]


def create_access_token(user_id: str) -> str:
    """Create a signed access token with jti (blocklist) and iat (revoke-epoch)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token."""
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM]
    )
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload
