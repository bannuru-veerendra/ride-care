from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.extensions import get_db
from app.models.user import User
from app.schemas.user import UserCreate, LoginRequest, UserResponse, TokenResponse
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(registration: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """Register a new user"""
    result = await db.execute(select(User).where(User.email == registration.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(
        email=registration.email,
        full_name=registration.full_name,
        hashed_password=hash_password(registration.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Login a user"""
    result = await db.execute(select(User).where(User.email == credentials.email))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(db_user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")
