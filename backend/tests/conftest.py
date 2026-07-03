import io
import uuid

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
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


@pytest.fixture(autouse=True)
def mock_document_storage(monkeypatch):
    """Mock Supabase storage so document tests run without external services."""

    async def fake_upload_document(file, vehicle_id, document_type):
        from app.utils.storage import ALLOWED_CONTENT_TYPES

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF, JPEG, JPG, and PNG files are allowed",
            )
        filename = file.filename or "file"
        extension = filename.rsplit(".", 1)[-1].lower()
        return f"{vehicle_id}/{document_type}_{uuid.uuid4()}.{extension}"

    async def fake_get_signed_url(storage_path, expires_in=3600):
        return f"https://fake-storage.example.com/{storage_path}?expires_in={expires_in}"

    async def fake_cleanup_document(path):
        return None

    async def fake_delete_document(path):
        return None

    async def fake_move_document(from_path, to_path):
        return to_path

    async def fake_relocate_document_type(storage_path, vehicle_id, new_document_type):
        extension = storage_path.rsplit(".", 1)[-1].lower()
        return f"{vehicle_id}/{new_document_type}_{uuid.uuid4()}.{extension}"

    for module in ("app.utils.storage", "app.routes.documents"):
        monkeypatch.setattr(f"{module}.upload_document", fake_upload_document)
        monkeypatch.setattr(f"{module}.get_signed_url", fake_get_signed_url)
        monkeypatch.setattr(f"{module}.cleanup_document", fake_cleanup_document)
        monkeypatch.setattr(f"{module}.move_document", fake_move_document)
        monkeypatch.setattr(f"{module}.relocate_document_type", fake_relocate_document_type)

    monkeypatch.setattr("app.utils.storage.delete_document", fake_delete_document)
    monkeypatch.setattr("app.routes.documents.delete_storage_document", fake_delete_document)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(test_session_maker):
    async with test_session_maker() as session:
        await session.execute(delete(Document))
        await session.execute(delete(FuelLog))
        await session.execute(delete(ServiceLog))
        await session.execute(delete(Vehicle))
        await session.execute(delete(User))
        await session.commit()
    yield
    async with test_session_maker() as session:
        await session.execute(delete(Document))
        await session.execute(delete(FuelLog))
        await session.execute(delete(ServiceLog))
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


@pytest_asyncio.fixture
async def created_document(client: AsyncClient, auth_headers: dict, created_vehicle: dict):
    """Create a document and return its response"""
    vehicle_id = created_vehicle["id"]
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content for testing")
    fake_pdf.name = "test_document.pdf"

    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={
            "document_type": "insurance",
            "expiry_date": "2026-01-01",
            "notes": "Test document",
        },
        files={"file": ("test_document.pdf", fake_pdf, "application/pdf")},
        headers=auth_headers,
    )
    return response.json()
