"""Request-ID middleware and access-log correlation."""

from __future__ import annotations

import logging

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_health_returns_request_id_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id
    assert len(request_id) >= 8


@pytest.mark.asyncio
async def test_incoming_request_id_is_echoed_when_safe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "client-trace-abc123"},
        )

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "client-trace-abc123"


@pytest.mark.asyncio
async def test_unsafe_incoming_request_id_is_replaced():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "bad id with spaces!"},
        )

    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id
    assert request_id != "bad id with spaces!"
    assert " " not in request_id


@pytest.mark.asyncio
async def test_access_log_includes_request_id(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="ridecare.access")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "access-log-trace-001"},
        )

    assert response.status_code == 200
    matching = [
        record
        for record in caplog.records
        if record.name == "ridecare.access"
        and "access-log-trace-001" in record.getMessage()
        and "path=/health" in record.getMessage()
        and "status=200" in record.getMessage()
    ]
    assert matching, "expected structured access log with request_id and latency"
