import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.auth_cookies import ACCESS_COOKIE
from app.utils.jwt import decode_access_token

# auto_error=False so we can fall back to the httpOnly access cookie
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from Bearer token or access cookie."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    access = token or request.cookies.get(ACCESS_COOKIE)
    if not access:
        raise credentials_exception

    try:
        payload = decode_access_token(access)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_uuid = uuid.UUID(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    db_user = result.scalar_one_or_none()
    if db_user is None or not db_user.is_active:
        raise credentials_exception
    return db_user
