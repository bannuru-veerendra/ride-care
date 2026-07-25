from fastapi import Request
from httpx import AsyncClient
from redis.asyncio import Redis

from app.utils.rate_limiter import (
    check_rate_limit,
    get_client_ip,
    get_user_id_from_request,
)

# Keep authenticated limit tests small so they finish well under the
# 15-minute access-token TTL (full-suite remote DB calls are slow).
_TEST_USER_LIMIT = 5


async def _user_rate_limit_for_tests(request: Request, redis: Redis) -> None:
    """Same as production user_rate_limit, with a tiny max for speed."""
    user_id = get_user_id_from_request(request)
    if user_id:
        key = f"rate_limit:user:{user_id}"
    else:
        key = f"rate_limit:ip_fallback:{get_client_ip(request)}"
    await check_rate_limit(
        redis,
        key,
        max_requests=_TEST_USER_LIMIT,
        window_seconds=60,
    )


async def test_login_rate_limit(client: AsyncClient, registered_user: dict):
    """
    Auth endpoints use IP-based limiting — 10 requests per minute.
    The 11th request should return 429.
    """
    payload = {
        "email": registered_user["email"],
        "password": "WrongPassword123!",
    }

    for _ in range(10):
        response = await client.post("/auth/login", json=payload)
        assert response.status_code in (200, 401)

    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 429
    assert "Too many" in response.json()["detail"]


async def test_register_rate_limit(client: AsyncClient):
    """
    Register endpoint uses IP-based limiting — 10 requests per minute.
    """
    for i in range(10):
        await client.post(
            "/auth/register",
            json={
                "email": f"user{i}@ridecare.com",
                "full_name": "Test User",
                "password": "TestPassword123!",
            },
        )

    response = await client.post(
        "/auth/register",
        json={
            "email": "user11@ridecare.com",
            "full_name": "Test User",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 429


async def test_user_rate_limit(client: AsyncClient, auth_headers: dict, monkeypatch):
    """
    Authenticated endpoints are limited per user_id.
    The request after the limit should return 429.
    Users on the same IP do not affect each other.
    """
    monkeypatch.setattr("main.user_rate_limit", _user_rate_limit_for_tests)

    for _ in range(_TEST_USER_LIMIT):
        response = await client.get("/vehicles/", headers=auth_headers)
        assert response.status_code == 200

    response = await client.get("/vehicles/", headers=auth_headers)
    assert response.status_code == 429


async def test_different_users_have_independent_limits(
    client: AsyncClient,
    auth_headers: dict,
    other_user_headers: dict,
    monkeypatch,
):
    """
    Two users on the same IP have independent rate limit counters.
    Exhausting one user's limit does not affect the other.
    """
    monkeypatch.setattr("main.user_rate_limit", _user_rate_limit_for_tests)

    for _ in range(_TEST_USER_LIMIT):
        await client.get("/vehicles/", headers=auth_headers)

    response = await client.get("/vehicles/", headers=auth_headers)
    assert response.status_code == 429

    response = await client.get("/vehicles/", headers=other_user_headers)
    assert response.status_code == 200


async def test_rate_limit_resets_per_endpoint(
    client: AsyncClient,
    registered_user: dict,
):
    """
    Auth rate limits are scoped per endpoint —
    hitting login limit does not affect register.
    """
    for _ in range(10):
        await client.post(
            "/auth/login",
            json={
                "email": registered_user["email"],
                "password": "WrongPassword123!",
            },
        )

    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@ridecare.com",
            "full_name": "New User",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 201
