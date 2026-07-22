from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: str) -> str:
    """Create an access token"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode an access token"""
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM]
    )
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload
