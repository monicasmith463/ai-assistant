"""API endpoints for document management."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user, rate_limiter
from ...core.db.database import async_get_db
from ...crud.crud_documents import crud_documents
from ...schemas.document import DocumentCreateInternal, DocumentRead, DocumentUpdateInternal
from ...services.document_processor import DocumentProcessor
from ...services.file_upload import FileUploadService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead, dependencies=[Depends(rate_limiter)])
async def upload_document(
    file: UploadFile = File(...),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Upload and process a document.

    Args:
        file: The document file to upload
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created document information

    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        # Validate and save file
        file_path, original_filename = await FileUploadService.save_uploaded_file(file)

        # Get file info
        file_type = DocumentProcessor.validate_file_type(original_filename)
        file_size = FileUploadService.get_file_size(file_path)

        # Extract text content
        file_content = await FileUploadService.get_file_content(file_path)
        extracted_text = await DocumentProcessor.process_document(file_content, file_type)

        # Create document record
        document_data = DocumentCreateInternal(
            title=original_filename.rsplit('.', 1)[0],  # Remove extension for title
            filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            content=extracted_text,
            user_id=current_user["id"]
        )

        document = await crud_documents.create(session, object=document_data)
        return document

    except HTTPException:
        # Clean up file if document creation fails
        try:
            await FileUploadService.delete_file(file_path)
        except Exception:
            pass
        raise
    except Exception as e:
        # Clean up file if processing fails
        try:
            await FileUploadService.delete_file(file_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.get("/", response_model=list[DocumentRead])
async def get_user_documents(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get all documents for current user.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of user's documents
    """
    documents = await crud_documents.get_multi(
        session,
        user_id=current_user["id"],
        is_deleted=False
    )
    return documents


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get specific document.

    Args:
        document_id: ID of the document to retrieve
        current_user: Current authenticated user
        session: Database session

    Returns:
        Document information

    Raises:
        HTTPException: If document not found or access denied
    """
    document = await crud_documents.get(
        session,
        id=document_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.put("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: int,
    title: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Update document title.

    Args:
        document_id: ID of the document to update
        title: New title for the document
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated document information

    Raises:
        HTTPException: If document not found or access denied
    """
    # Check if document exists and belongs to user
    document = await crud_documents.get(
        session,
        id=document_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update document
    update_data = DocumentUpdateInternal(
        title=title,
        updated_at=datetime.now(UTC)
    )

    updated_document = await crud_documents.update(session, object=update_data, id=document_id)
    return updated_document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Delete a document.

    Args:
        document_id: ID of the document to delete
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or access denied
    """
    # Check if document exists and belongs to user
    document = await crud_documents.get(
        session,
        id=document_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Soft delete the document
    await crud_documents.db_delete(session, id=document_id)

    # Delete the physical file
    try:
        await FileUploadService.delete_file(document["file_path"])
    except Exception:
        # Log error but don't fail the request
        pass

    return {"message": "Document deleted successfully"}
