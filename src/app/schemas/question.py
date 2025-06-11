from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class QuestionBase(BaseModel):
    question_text: Annotated[str, Field(min_length=1, examples=["What is the main topic of this document?"])]
    question_type: Annotated[str, Field(min_length=1, max_length=50, examples=["multiple_choice"])]
    correct_answer: Annotated[str, Field(min_length=1, examples=["Option A"])]
    options: Annotated[str | None, Field(examples=['["Option A", "Option B", "Option C", "Option D"]'], default=None)]
    explanation: Annotated[str | None, Field(examples=["This is correct because..."], default=None)]
    difficulty: Annotated[str, Field(max_length=20, examples=["medium"], default="medium")]


class Question(TimestampSchema, QuestionBase, UUIDSchema, PersistentDeletion):
    document_id: int
    user_id: int


class QuestionRead(BaseModel):
    id: int
    question_text: str
    question_type: str
    correct_answer: str
    options: str | None
    explanation: str | None
    difficulty: str
    document_id: int
    created_at: datetime
    updated_at: datetime | None


class QuestionCreate(QuestionBase):
    model_config = ConfigDict(extra="forbid")

    document_id: int


class QuestionCreateInternal(QuestionBase):
    document_id: int
    user_id: int


class QuestionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_text: Annotated[str | None, Field(min_length=1, examples=["Updated question?"], default=None)]
    question_type: Annotated[str | None, Field(min_length=1, max_length=50, examples=["short_answer"], default=None)]
    correct_answer: Annotated[str | None, Field(min_length=1, examples=["Updated answer"], default=None)]
    options: Annotated[str | None, Field(examples=['["New Option A", "New Option B"]'], default=None)]
    explanation: Annotated[str | None, Field(examples=["Updated explanation..."], default=None)]
    difficulty: Annotated[str | None, Field(max_length=20, examples=["hard"], default=None)]


class QuestionUpdateInternal(QuestionUpdate):
    updated_at: datetime


class QuestionDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class QuestionRestoreDeleted(BaseModel):
    is_deleted: bool
