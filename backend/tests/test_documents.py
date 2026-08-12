import io
from datetime import date, timedelta

from httpx import AsyncClient


def make_fake_pdf(content: bytes = b"%PDF-1.4 fake pdf content for testing"):
    """Helper function to create a fake PDF file for testing"""
    return ("test.pdf", io.BytesIO(content), "application/pdf")


def make_fake_jpeg():
    """Helper function to create a fake JPEG file for testing"""
    return ("test.jpeg", io.BytesIO(b"fake jpeg content for testing"), "image/jpeg")


def make_fake_png():
    """Helper function to create a fake PNG file for testing"""
    return ("test.png", io.BytesIO(b"fake png content for testing"), "image/png")


def make_fake_txt():
    """Helper function to create a fake TXT file for testing"""
    return ("test.txt", io.BytesIO(b"fake txt content for testing"), "text/plain")


async def test_upload_document_success(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test uploading a document successfully"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={
            "document_type": "insurance",
            "expiry_date": "2026-01-01",
            "notes": "Test document",
        },
        files={"file": make_fake_pdf()},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["document_type"] == "insurance"
    assert data["original_filename"] == "test.pdf"
    assert data["expiry_date"] == "2026-01-01"
    assert data["notes"] == "Test document"
    assert "signed_url" in data
    assert "id" in data
    assert data["days_until"] is not None
    assert data["expiry_status"] in ("ok", "soon", "expired")


async def test_upload_driving_license(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test uploading a driving license document successfully"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "driving_license"},
        files={"file": make_fake_pdf()},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["document_type"] == "driving_license"


async def test_upload_rc(client: AsyncClient, auth_headers: dict, created_vehicle: dict):
    """Test uploading a registration certificate document successfully"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "registration_certificate"},
        files={"file": make_fake_png()},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["document_type"] == "registration_certificate"


async def test_upload_image_document(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test uploading an image document successfully"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "insurance"},
        files={"file": make_fake_jpeg()},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["original_filename"] == "test.jpeg"


async def test_upload_disallowed_file_type(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test uploading a document with a disallowed file type returns 400"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "insurance"},
        files={"file": make_fake_txt()},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "allowed" in response.json()["detail"].lower()


async def test_upload_invalid_document_type(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test uploading a document with an invalid document type returns 422"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "invalid_type"},
        files={"file": make_fake_pdf()},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_upload_document_nonexistent_vehicle(
    client: AsyncClient, auth_headers: dict
):
    """Test uploading a document for a non-existent vehicle returns 404"""
    vehicle_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "insurance"},
        files={"file": make_fake_pdf()},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_get_documents(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test getting documents successfully"""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["has_more"] is False
    assert data["next_cursor"] is None
    assert data["items"][0]["id"] == created_document["id"]
    assert data["items"][0]["signed_url"].startswith("https://")


async def test_get_document_by_id(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test getting a document by id successfully"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.get(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert data["signed_url"].startswith("https://")


async def test_get_document_not_found(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test getting a document by id with a non-existent id returns 404"""
    vehicle_id = created_vehicle["id"]
    document_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_update_document_expiry_date(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test updating a document expiry date successfully"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    new_expiry_date = str(date.today() + timedelta(days=365))
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={"expiry_date": new_expiry_date},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["expiry_date"] == new_expiry_date


async def test_update_document_notes(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test updating document notes successfully"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={"notes": "Updated notes for the document"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated notes for the document"


async def test_update_document_clear_expiry_and_notes(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Clear flags remove expiry_date and notes."""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    assert created_document["expiry_date"] is not None

    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={"clear_expiry_date": "true", "clear_notes": "true"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expiry_date"] is None
    assert data["notes"] is None


async def test_update_document_replace_file(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test replacing a document file successfully"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    original_filename = created_document["original_filename"]
    original_signed_url = created_document["signed_url"]
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        files={
            "file": (
                "new_insurance.pdf",
                io.BytesIO(b"new insurance content for testing"),
                "application/pdf",
            )
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert data["original_filename"] == "new_insurance.pdf"
    assert data["original_filename"] != original_filename
    assert data["signed_url"].startswith("https://")
    assert data["signed_url"] != original_signed_url


async def test_update_document_type(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test updating a document type successfully"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "driving_license"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["document_type"] == "driving_license"


async def test_update_document_empty_patch(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test updating a document with an empty patch returns 400"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "at least one field" in response.json()["detail"].lower()


async def test_update_document_not_found(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test updating a document with a non-existent id returns 404"""
    vehicle_id = created_vehicle["id"]
    document_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={"notes": "Should not apply"},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_document(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict, created_document: dict
):
    """Test deleting a document successfully"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.delete(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 204

    response = await client.get(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_cannot_access_other_users_documents(
    client: AsyncClient, created_vehicle: dict, other_user_headers: dict
):
    """Test that a user cannot access another user's documents"""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_cannot_get_other_users_document_by_id(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    created_document: dict,
    other_user_headers: dict,
):
    """Test that a user cannot get another user's document by id"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.get(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_cannot_update_other_users_document(
    client: AsyncClient,
    created_vehicle: dict,
    created_document: dict,
    other_user_headers: dict,
):
    """Test that a user cannot update another user's document"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.patch(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        data={"notes": "Unauthorized update"},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_cannot_delete_other_users_document(
    client: AsyncClient,
    created_vehicle: dict,
    created_document: dict,
    other_user_headers: dict,
):
    """Test that a user cannot delete another user's document"""
    vehicle_id = created_vehicle["id"]
    document_id = created_document["id"]
    response = await client.delete(
        f"/documents/{document_id}",
        params={"vehicle_id": vehicle_id},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_upload_without_token(client: AsyncClient, created_vehicle: dict):
    """Test uploading a document without a token returns 401"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={"document_type": "insurance"},
        files={"file": make_fake_pdf()},
    )
    assert response.status_code == 401


async def test_get_documents_cursor_pagination(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Cursor-paginated document list returns non-overlapping pages."""
    vehicle_id = created_vehicle["id"]
    document_types = [
        "insurance",
        "driving_license",
        "registration_certificate",
        "insurance",
        "driving_license",
    ]

    for index, document_type in enumerate(document_types):
        response = await client.post(
            "/documents/",
            params={"vehicle_id": vehicle_id},
            data={"document_type": document_type},
            files={"file": make_fake_pdf(f"doc-{index}".encode())},
            headers=auth_headers,
        )
        assert response.status_code == 201

    page1 = await client.get(
        "/documents/",
        params={"vehicle_id": vehicle_id, "size": 3},
        headers=auth_headers,
    )
    data1 = page1.json()
    assert len(data1["items"]) == 3
    assert data1["has_more"] is True
    assert data1["next_cursor"] is not None
    assert data1["total"] == 5

    page2 = await client.get(
        "/documents/",
        params={
            "vehicle_id": vehicle_id,
            "size": 3,
            "cursor": data1["next_cursor"],
        },
        headers=auth_headers,
    )
    data2 = page2.json()
    assert len(data2["items"]) == 2
    assert data2["has_more"] is False

    page1_ids = {item["id"] for item in data1["items"]}
    page2_ids = {item["id"] for item in data2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


async def test_get_documents_without_token(client: AsyncClient, created_vehicle: dict):
    """Test getting documents without a token returns 401"""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        "/documents/",
        params={"vehicle_id": vehicle_id},
    )
    assert response.status_code == 401
