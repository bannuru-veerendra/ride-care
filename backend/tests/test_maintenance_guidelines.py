from httpx import AsyncClient


async def test_get_guidelines(client: AsyncClient, auth_headers: dict):
    """Returns all maintenance guidelines."""
    response = await client.get(
        "/maintenance-guidelines/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 24

    first = data[0]
    assert "component" in first
    assert "task" in first
    assert "description" in first
    assert "severity" in first
    assert "sort_order" in first
    assert "interval_km" in first
    assert "interval_months" in first


async def test_guidelines_require_auth(client: AsyncClient):
    """Unauthenticated request returns 401."""
    response = await client.get("/maintenance-guidelines/")
    assert response.status_code == 401


async def test_filter_by_severity(client: AsyncClient, auth_headers: dict):
    """Severity filter returns only matching guidelines."""
    response = await client.get(
        "/maintenance-guidelines/",
        params={"severity": "critical"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(g["severity"] == "critical" for g in data)


async def test_filter_by_component(client: AsyncClient, auth_headers: dict):
    """Component filter returns only matching guidelines."""
    response = await client.get(
        "/maintenance-guidelines/",
        params={"component": "Engine"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(g["component"] == "Engine" for g in data)


async def test_filter_case_insensitive(client: AsyncClient, auth_headers: dict):
    """Component filter is case insensitive."""
    response = await client.get(
        "/maintenance-guidelines/",
        params={"component": "engine"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


async def test_filter_combined(client: AsyncClient, auth_headers: dict):
    """Severity and component filters can be combined."""
    response = await client.get(
        "/maintenance-guidelines/",
        params={"severity": "high", "component": "Engine"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert all(
        g["severity"] == "high" and g["component"] == "Engine" for g in data
    )


async def test_filter_no_results(client: AsyncClient, auth_headers: dict):
    """Filter with no matches returns empty list not 404."""
    response = await client.get(
        "/maintenance-guidelines/",
        params={"severity": "nonexistent"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_guidelines_ordered_by_sort_order(
    client: AsyncClient, auth_headers: dict
):
    """Guidelines are returned in sort_order ascending."""
    response = await client.get(
        "/maintenance-guidelines/",
        headers=auth_headers,
    )
    data = response.json()
    sort_orders = [g["sort_order"] for g in data]
    assert sort_orders == sorted(sort_orders)


async def test_get_components(client: AsyncClient, auth_headers: dict):
    """Returns unique component names in order."""
    response = await client.get(
        "/maintenance-guidelines/components",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert len(data) == len(set(data))
    assert "Engine" in data
    assert "Brakes" in data


async def test_get_severity_levels(client: AsyncClient, auth_headers: dict):
    """Returns severity levels in priority order."""
    response = await client.get(
        "/maintenance-guidelines/severity-levels",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data == ["critical", "high", "medium", "low"]


async def test_guidelines_consistent(client: AsyncClient, auth_headers: dict):
    """Two requests return identical data — loaded from memory."""
    response1 = await client.get(
        "/maintenance-guidelines/",
        headers=auth_headers,
    )
    response2 = await client.get(
        "/maintenance-guidelines/",
        headers=auth_headers,
    )
    assert response1.json() == response2.json()
