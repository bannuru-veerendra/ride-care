from httpx import AsyncClient


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


async def test_user_rate_limit(client: AsyncClient, auth_headers: dict):
    """
    Authenticated endpoints are limited per user_id — 100 req/min.
    The 101st request should return 429.
    Users on the same IP do not affect each other.
    """
    for _ in range(100):
        response = await client.get("/vehicles/", headers=auth_headers)
        assert response.status_code == 200

    response = await client.get("/vehicles/", headers=auth_headers)
    assert response.status_code == 429


async def test_different_users_have_independent_limits(
    client: AsyncClient,
    auth_headers: dict,
    other_user_headers: dict,
):
    """
    Two users on the same IP have independent rate limit counters.
    Exhausting one user's limit does not affect the other.
    """
    for _ in range(100):
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
