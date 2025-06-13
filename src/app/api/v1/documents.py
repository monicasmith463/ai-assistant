from typing import Annotated, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
import os
import fitz  # PyMuPDF
from src.app.api.dependencies import async_get_db
from ...schemas.document import DocumentRead, DocumentCreate, DocumentCreateInternal
from src.app.api.v1.documents import crud_documents
from ...core.db.database import async_get_db

from typing import Annotated, Any


from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import DuplicateValueException, ForbiddenException, NotFoundException
from ...core.security import blacklist_token, get_password_hash, oauth2_scheme
from ...crud.crud_rate_limit import crud_rate_limits
from ...crud.crud_tier import crud_tiers
from ...crud.crud_users import crud_users
from ...models.tier import Tier
from ...schemas.tier import TierRead
from ...schemas.user import UserRead


router = APIRouter(tags=["documents"])


@router.post("/document", response_model=DocumentRead, status_code=201)
async def create_upload_document(
         request: Request,
    document: DocumentCreate,
    file: UploadFile = File(...),
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DocumentRead:
        


        # try:
            # Read the PDF file content
            # contents = await file.read()

            # Generate a unique key for the S3 object
            # You can use the original filename or generate a UUID
            # For simplicity, using the original filename here
            # s3_key = file.filename

            # Upload the file to S3
            # s3.put_object(Body=contents, Bucket=S3_BUCKET_NAME, Key=s3_key, ContentType="application/pdf")

        #     return await crud_documents.create(
        #         db=db,
        #         object=DocumentCreate(
        #             filename=file.filename,
        #             content_type=file.content_type,
        #             size=file.size,
        #             s3_url=f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}",
        #             created_by_user_id=1  # Replace with actual user ID from request context
        #         )
        #     )

        # except Exception as e:
        #     print(f"Error uploading file: {e}")

    # TODO: s3 upload handle this later
    document_internal_dict = document.model_dump()
    document_internal_dict["created_by_user_id"] = current_user["id"]
    document_internal_dict["s3_url"] = None

    document_internal = DocumentCreateInternal(**document_internal_dict)
    created_document: DocumentRead = await crud_documents.create(db=db, object=document_internal)
    return created_document

