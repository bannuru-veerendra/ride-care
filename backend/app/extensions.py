from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from sqlalchemy.orm import DeclarativeBase

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

async def get_db():
    """Dependency to get a database session"""
    async with AsyncSessionLocal() as session:
        yield session