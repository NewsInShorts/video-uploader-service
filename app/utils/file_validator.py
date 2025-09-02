from fastapi import UploadFile, HTTPException
import os, logging

logger = logging.getLogger(__name__)

def validate_file(file: UploadFile, allowed_extensions: list, max_size_mb: int):
    """Validate file type and size before processing."""
    extension = file.filename.split(".")[-1].lower()
    if extension not in allowed_extensions:
        logger.warning(f"Invalid file type attempted: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{extension}'. Allowed: {allowed_extensions}"
        )

    file.file.seek(0, os.SEEK_END)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)
    if size_mb > max_size_mb:
        logger.warning(f"File too large: {file.filename} ({size_mb:.2f} MB)")
        raise HTTPException(
            status_code=400,
            detail=f"File size {size_mb:.2f} MB exceeds max {max_size_mb} MB"
        )
