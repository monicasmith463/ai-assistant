"""File upload service for handling document uploads securely."""

import os
import uuid
from pathlib import Path
# Removed typing import - using built-in types

import aiofiles
from fastapi import HTTPException, UploadFile

from ..core.config import settings
from ..core.logger import logging

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads and storage."""

    @staticmethod
    async def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
        """Save uploaded file and return file path and filename.

        Args:
            file: FastAPI UploadFile object

        Returns:
            Tuple of (file_path, original_filename)

        Raises:
            HTTPException: If file saving fails
        """
        try:
            # Validate file first
            FileUploadService.validate_file(file)

            # Create uploads directory if it doesn't exist
            upload_dir = Path(settings.DOCUMENT_STORAGE_PATH)
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename to avoid conflicts
            file_extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename

            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            logger.info(f"Successfully saved file: {file.filename} as {unique_filename}")
            return str(file_path), file.filename

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validate file type and size.

        Args:
            file: FastAPI UploadFile object

        Raises:
            HTTPException: If file validation fails
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file extension
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_extension}' not allowed. "
                f"Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )

        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if file.size > max_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds "
                    f"maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB)"
                )

    @staticmethod
    async def delete_file(file_path: str) -> None:
        """Delete file from storage.

        Args:
            file_path: Path to the file to delete

        Raises:
            Exception: If file deletion fails
        """
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_path_obj.unlink()
                logger.info(f"Successfully deleted file: {file_path}")
            else:
                logger.warning(f"File not found for deletion: {file_path}")

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")

    @staticmethod
    async def get_file_content(file_path: str) -> bytes:
        """Read file content from storage.

        Args:
            file_path: Path to the file

        Returns:
            File content as bytes

        Raises:
            Exception: If file reading fails
        """
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise Exception(f"Failed to read file: {str(e)}")

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes

        Raises:
            Exception: If file doesn't exist
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size for {file_path}: {str(e)}")
            raise Exception(f"Failed to get file size: {str(e)}")

    @staticmethod
    def ensure_upload_directory() -> None:
        """Ensure upload directory exists."""
        upload_dir = Path(settings.DOCUMENT_STORAGE_PATH)
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory ensured: {upload_dir}")
