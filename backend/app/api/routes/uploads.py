"""
Uploads API Routes - File upload handling.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Supported image types
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Upload directory
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file."""
    # Check extension
    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")


@router.post("/image")
async def upload_image(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> dict:
    """Upload an image file. Returns the URL to access the image."""
    validate_image(file)

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Generate unique filename
    ext = get_file_extension(file.filename or "unknown.png")
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Return URL
    return {
        "filename": unique_filename,
        "url": f"/api/v1/uploads/files/{unique_filename}",
        "size": len(content),
        "content_type": file.content_type,
    }


@router.get("/files/{filename}")
async def get_file(filename: str) -> FileResponse:
    """Serve an uploaded file."""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Security check - ensure file is within upload directory
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(file_path)
