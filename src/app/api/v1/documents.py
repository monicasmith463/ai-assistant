from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db.database import async_get_db
from ...schemas.document import DocumentRead, DocumentCreate, DocumentCreateInternal
from ...core.exceptions.http_exceptions import CustomException
from typing import Annotated, Any
from ...api.dependencies import get_current_user
from ...crud.crud_documents import crud_documents
from ...schemas.user import UserRead
from ...core.logger import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"]) 

@router.post("/document", response_model=DocumentRead, status_code=201)
async def create_document(
    document: DocumentCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DocumentRead:
    try:
        document_internal_dict = document.model_dump()
        document_internal_dict["created_by_user_id"] = current_user["id"]

        document_internal = DocumentCreateInternal(**document_internal_dict)
        created_document: DocumentRead = await crud_documents.create(db=db, object=document_internal)
        return created_document
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise CustomException(500, "Internal server error while creating document.")