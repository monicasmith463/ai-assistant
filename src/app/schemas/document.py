from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class DocumentBase(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200, examples=["My Study Document"])]
    filename: Annotated[str, Field(min_length=1, max_length=255, examples=["document.pdf"])]
    file_path: Annotated[str, Field(min_length=1, max_length=500, examples=["/uploads/documents/document.pdf"])]
    file_type: Annotated[str, Field(min_length=1, max_length=10, examples=["pdf"])]
    file_size: Annotated[int, Field(gt=0, examples=[1024000])]


class Document(TimestampSchema, DocumentBase, UUIDSchema, PersistentDeletion):
    content: str | None = None
    user_id: int


class DocumentRead(BaseModel):
    id: int
    title: Annotated[str, Field(min_length=1, max_length=200, examples=["My Study Document"])]
    filename: Annotated[str, Field(min_length=1, max_length=255, examples=["document.pdf"])]
    file_type: Annotated[str, Field(min_length=1, max_length=10, examples=["pdf"])]
    file_size: Annotated[int, Field(gt=0, examples=[1024000])]
    content: str | None
    created_at: datetime
    updated_at: datetime | None


class DocumentCreate(DocumentBase):
    model_config = ConfigDict(extra="forbid")


class DocumentCreateInternal(DocumentBase):
    user_id: int


class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(min_length=1, max_length=200, examples=["Updated Document"], default=None)]
    content: Annotated[str | None, Field(examples=["Extracted document content..."], default=None)]


class DocumentUpdateInternal(DocumentUpdate):
    updated_at: datetime


class DocumentDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class DocumentRestoreDeleted(BaseModel):
    is_deleted: bool
