import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.models.fuel_log import FuelLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.service_log import ServiceLog
from app.models.document import Document
from main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_maker(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(test_session_maker):
    async with test_session_maker() as session:
        await session.execute(delete(Document))
        await session.execute(delete(ServiceLog))
        await session.execute(delete(FuelLog))
        await session.execute(delete(Vehicle))
        await session.execute(delete(User))
        await session.commit()
    yield
    async with test_session_maker() as session:
        await session.execute(delete(Document))
        await session.execute(delete(ServiceLog))
        await session.execute(delete(FuelLog))
        await session.execute(delete(Vehicle))
        await session.execute(delete(User))
        await session.commit()


@pytest_asyncio.fixture
async def client(test_session_maker):
    async def override_get_db():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    """Create a user and return their credentials"""
    payload = {
        "email": "test@ridecare.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
    }
    await client.post("/auth/register", json=payload)
    return payload


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict):
    """Authenticate the client with the registered user"""
    response = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    tokens = response.json()["access_token"]
    return {"Authorization": f"Bearer {tokens}"}


@pytest_asyncio.fixture
async def other_user_headers(client: AsyncClient):
    """Register a second user and return their auth headers"""
    await client.post(
        "/auth/register",
        json={
            "email": "otheruser@ridecare.com",
            "full_name": "Other User",
            "password": "OtherPass123",
        },
    )
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "otheruser@ridecare.com",
            "password": "OtherPass123",
        },
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


@pytest_asyncio.fixture
async def created_vehicle(client: AsyncClient, auth_headers: dict):
    """Create a vehicle and return its response"""
    payload = {
        "brand": "Test Brand",
        "vehicle_name": "Test Vehicle",
        "year": 2020,
        "registration_number": "1234567890",
        "current_odometer": 10000,
    }
    response = await client.post("/vehicles/", json=payload, headers=auth_headers)
    return response.json()
