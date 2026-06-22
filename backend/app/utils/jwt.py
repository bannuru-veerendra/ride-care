from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day


def create_access_token(data: dict) -> str:
    """Create an access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode an access token"""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])