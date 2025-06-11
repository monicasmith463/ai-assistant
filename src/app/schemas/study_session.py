from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class StudySessionBase(BaseModel):
    session_name: Annotated[str, Field(min_length=1, max_length=200, examples=["Chapter 1 Practice"])]
    total_questions: Annotated[int, Field(gt=0, examples=[10])]
    correct_answers: Annotated[int, Field(ge=0, examples=[8], default=0)]
    score_percentage: Annotated[float | None, Field(ge=0, le=100, examples=[80.0], default=None)]
    time_spent_minutes: Annotated[int | None, Field(ge=0, examples=[15], default=None)]
    answers: Annotated[str | None, Field(examples=['[{"question_id": 1, "answer": "A", "correct": true}]'], default=None)]


class StudySession(TimestampSchema, StudySessionBase, UUIDSchema, PersistentDeletion):
    document_id: int
    user_id: int


class StudySessionRead(BaseModel):
    id: int
    session_name: str
    total_questions: int
    correct_answers: int
    score_percentage: float | None
    time_spent_minutes: int | None
    document_id: int
    created_at: datetime
    updated_at: datetime | None


class StudySessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_name: Annotated[str, Field(min_length=1, max_length=200, examples=["Chapter 1 Practice"])]
    total_questions: Annotated[int, Field(gt=0, examples=[10])]
    document_id: int


class StudySessionCreateInternal(StudySessionBase):
    document_id: int
    user_id: int


class StudySessionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_name: Annotated[str | None, Field(min_length=1, max_length=200, examples=["Updated Session"], default=None)]
    correct_answers: Annotated[int | None, Field(ge=0, examples=[9], default=None)]
    score_percentage: Annotated[float | None, Field(ge=0, le=100, examples=[90.0], default=None)]
    time_spent_minutes: Annotated[int | None, Field(ge=0, examples=[20], default=None)]
    answers: Annotated[str | None, Field(examples=['[{"question_id": 1, "answer": "B", "correct": false}]'], default=None)]


class StudySessionUpdateInternal(StudySessionUpdate):
    updated_at: datetime


class StudySessionDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class StudySessionRestoreDeleted(BaseModel):
    is_deleted: bool
