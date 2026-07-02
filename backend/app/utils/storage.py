import logging
import uuid

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/jpg"}
MAX_FILE_SIZE_MB = 10


def _bucket():
    return get_supabase_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)


def build_storage_path(vehicle_id: uuid.UUID, document_type: str, extension: str) -> str:
    """Build a new storage object path for a document."""
    return f"{vehicle_id}/{document_type}_{uuid.uuid4()}.{extension}"


async def upload_document(file: UploadFile, vehicle_id: uuid.UUID, document_type: str) -> str:
    """Upload a document to Supabase Storage."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, JPEG, JPG, and PNG files are allowed",
        )
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be under {MAX_FILE_SIZE_MB}MB",
        )

    filename = file.filename or "file"
    extension = filename.rsplit(".", 1)[-1].lower()
    storage_path = build_storage_path(vehicle_id, document_type, extension)

    _bucket().upload(
        storage_path,
        contents,
        file_options={"content-type": file.content_type},
    )
    return storage_path


async def move_document(from_path: str, to_path: str) -> str:
    """Move a stored object to a new path within the bucket."""
    _bucket().move(from_path, to_path)
    return to_path


async def relocate_document_type(
    storage_path: str,
    vehicle_id: uuid.UUID,
    new_document_type: str,
) -> str:
    """Move a file so its storage path matches an updated document type."""
    extension = storage_path.rsplit(".", 1)[-1].lower()
    new_path = build_storage_path(vehicle_id, new_document_type, extension)
    return await move_document(storage_path, new_path)


async def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """Get the URL of a document from Supabase Storage."""
    result = _bucket().create_signed_url(storage_path, expires_in)
    signed_url = result.get("signedUrl")
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate document URL",
        )
    return signed_url


async def delete_document(path: str) -> None:
    """Delete a document from Supabase Storage."""
    _bucket().remove([path])


async def cleanup_document(path: str) -> None:
    """Best-effort storage cleanup; logs failures without raising."""
    try:
        await delete_document(path)
    except Exception:
        logger.exception("Failed to remove storage object at %s", path)
