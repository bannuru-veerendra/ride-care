from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    """Test the register user endpoint"""
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@ridecare.com",
            "full_name": "Test User",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@ridecare.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient):
    """Test the register user endpoint with a duplicate email"""
    payload = {
        "email": "test@ridecare.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


async def test_login_success(client: AsyncClient, registered_user: dict):
    """Login sets httpOnly cookies; JSON body does not expose tokens."""
    response = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" not in data
    assert "refresh_token" not in data
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


async def test_cookie_auth_protects_routes(client: AsyncClient, registered_user: dict):
    """After login, access cookie alone authorizes API calls (no Authorization header)."""
    login_response = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert login_response.status_code == 200

    response = await client.get("/vehicles/")
    assert response.status_code == 200


async def test_refresh_via_cookie(client: AsyncClient, registered_user: dict):
    """Refresh works with the httpOnly refresh cookie and no body token."""
    await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    refresh_response = await client.post("/auth/refresh", json={})
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" not in data
    assert "access_token" in refresh_response.cookies
    assert "refresh_token" in refresh_response.cookies


async def test_logout_clears_cookies(client: AsyncClient, registered_user: dict):
    """Logout revokes the session and clears auth cookies."""
    await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    logout_response = await client.post("/auth/logout", json={})
    assert logout_response.status_code == 204

    refresh_response = await client.post("/auth/refresh", json={})
    assert refresh_response.status_code == 401


async def test_refresh_token_rotation(client: AsyncClient, registered_user: dict):
    """Refresh rotates cookies and invalidates the old refresh token."""
    login_response = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    old_refresh = login_response.cookies["refresh_token"]

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_response.status_code == 200
    new_refresh = refresh_response.cookies["refresh_token"]
    assert new_refresh != old_refresh

    reuse_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse_response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient, registered_user: dict):
    """Logout revokes the refresh token so it cannot be reused."""
    login_response = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    refresh_token = login_response.cookies["refresh_token"]

    logout_response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


async def test_oauth_token_returns_bearer_body(client: AsyncClient, registered_user: dict):
    """Swagger `/auth/token` still returns tokens in the JSON body."""
    response = await client.post(
        "/auth/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "access_token" in response.cookies


async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    """Test the login user endpoint with wrong password"""
    response = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    """Test the login user endpoint with nonexistent email"""
    response = await client.post(
        "/auth/login",
        json={
            "email": "nonexistent@ridecare.com",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 401


async def test_protected_route_without_token(client: AsyncClient):
    """Test a protected route without a token"""
    response = await client.get("/vehicles/")
    assert response.status_code == 401


async def test_protected_route_with_invalid_token(client: AsyncClient):
    """Test a protected route with an invalid token"""
    response = await client.get(
        "/vehicles/",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


async def test_register_short_password(client: AsyncClient):
    """Test the register user endpoint with a password that is too short"""
    response = await client.post(
        "/auth/register",
        json={
            "email": "shortpass@ridecare.com",
            "full_name": "Test User",
            "password": "short",
        },
    )
    assert response.status_code == 422


async def test_register_weak_password(client: AsyncClient):
    """Reject passwords missing uppercase, number, or special character."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "weakpass@ridecare.com",
            "full_name": "Test User",
            "password": "password123",
        },
    )
    assert response.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    """Test the register user endpoint with an invalid email"""
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 422

async def test_create_vehicle_without_token(client: AsyncClient):
    """Test creating a vehicle without authentication"""
    response = await client.post(
        "/vehicles/",
        json={
            "brand": "Honda",
            "vehicle_name": "Shine 100",
            "year": 2022,
            "registration_number": "TS09CD5678",
            "baseline_odometer": 3000,
        },
    )
    assert response.status_code == 401


async def test_create_fuel_log_without_token(client: AsyncClient):
    """Test creating a fuel log without authentication"""
    response = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": "00000000-0000-0000-0000-000000000000"},
        json={
            "date": "2024-01-01",
            "odometer": 1000,
            "total_cost": 800,
            "price_per_liter": 110,
        },
    )
    assert response.status_code == 401

