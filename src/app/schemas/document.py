from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class DocumentBase(BaseModel):
    filename: str
    content_type: str
    size: int
    s3_url: Optional[str] = None

class DocumentCreate(BaseModel):
    filename: str
    content_type: str
    size: int
    s3_url: Optional[str] = None


class DocumentCreateInternal(DocumentCreate):
    created_by_user_id: int


class DocumentRead(DocumentBase):
    uuid: uuid.UUID
    s3_url: str
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_deleted: bool

class DocumentUpdate(DocumentBase):
    pass


