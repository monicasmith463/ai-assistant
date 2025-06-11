"""CRUD operations for study sessions."""

from fastcrud import FastCRUD

from ..models.study_session import StudySession
from ..schemas.study_session import (
    StudySessionCreateInternal,
    StudySessionDelete,
    StudySessionUpdate,
    StudySessionUpdateInternal,
)

CRUDStudySession = FastCRUD[StudySession, StudySessionCreateInternal, StudySessionUpdate, StudySessionUpdateInternal, StudySessionDelete]
crud_study_sessions = CRUDStudySession(StudySession)
