"""API endpoints for study session management."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...crud.crud_documents import crud_documents
from ...crud.crud_study_sessions import crud_study_sessions
from ...schemas.study_session import (
    StudySessionCreate,
    StudySessionCreateInternal,
    StudySessionRead,
    StudySessionUpdate,
    StudySessionUpdateInternal,
)

router = APIRouter(prefix="/study-sessions", tags=["study-sessions"])


@router.post("/", response_model=StudySessionRead)
async def create_study_session(
    session_data: StudySessionCreate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Create a new study session.

    Args:
        session_data: Study session creation data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created study session

    Raises:
        HTTPException: If document not found or access denied
    """
    # Check if document exists and belongs to user
    document = await crud_documents.get(
        session,
        id=session_data.document_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Create study session
    study_session_create = StudySessionCreateInternal(
        session_name=session_data.session_name,
        total_questions=session_data.total_questions,
        document_id=session_data.document_id,
        user_id=current_user["id"]
    )

    study_session = await crud_study_sessions.create(session, object=study_session_create)
    return study_session


@router.get("/", response_model=list[StudySessionRead])
async def get_user_study_sessions(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get all study sessions for current user.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of user's study sessions
    """
    study_sessions = await crud_study_sessions.get_multi(
        session,
        user_id=current_user["id"],
        is_deleted=False
    )
    return study_sessions


@router.get("/{session_id}", response_model=StudySessionRead)
async def get_study_session(
    session_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get a specific study session.

    Args:
        session_id: ID of the study session
        current_user: Current authenticated user
        session: Database session

    Returns:
        Study session information

    Raises:
        HTTPException: If study session not found or access denied
    """
    study_session = await crud_study_sessions.get(
        session,
        id=session_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not study_session:
        raise HTTPException(status_code=404, detail="Study session not found")

    return study_session


@router.put("/{session_id}", response_model=StudySessionRead)
async def update_study_session(
    session_id: int,
    session_data: StudySessionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Update study session with results.

    Args:
        session_id: ID of the study session to update
        session_data: Study session update data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated study session

    Raises:
        HTTPException: If study session not found or access denied
    """
    # Check if study session exists and belongs to user
    study_session = await crud_study_sessions.get(
        session,
        id=session_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not study_session:
        raise HTTPException(status_code=404, detail="Study session not found")

    # Calculate score percentage if correct answers provided
    score_percentage = session_data.score_percentage
    if session_data.correct_answers is not None and score_percentage is None:
        total_questions = study_session["total_questions"]
        if total_questions > 0:
            score_percentage = (session_data.correct_answers / total_questions) * 100

    # Update study session
    update_data = StudySessionUpdateInternal(
        session_name=session_data.session_name,
        correct_answers=session_data.correct_answers,
        score_percentage=score_percentage,
        time_spent_minutes=session_data.time_spent_minutes,
        answers=session_data.answers,
        updated_at=datetime.now(UTC)
    )

    updated_session = await crud_study_sessions.update(session, object=update_data, id=session_id)
    return updated_session


@router.delete("/{session_id}")
async def delete_study_session(
    session_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Delete a study session.

    Args:
        session_id: ID of the study session to delete
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If study session not found or access denied
    """
    # Check if study session exists and belongs to user
    study_session = await crud_study_sessions.get(
        session,
        id=session_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not study_session:
        raise HTTPException(status_code=404, detail="Study session not found")

    # Soft delete the study session
    await crud_study_sessions.db_delete(session, id=session_id)

    return {"message": "Study session deleted successfully"}


@router.get("/document/{document_id}", response_model=list[StudySessionRead])
async def get_study_sessions_for_document(
    document_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get all study sessions for a specific document.

    Args:
        document_id: ID of the document
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of study sessions for the document

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

    # Get study sessions for the document
    study_sessions = await crud_study_sessions.get_multi(
        session,
        document_id=document_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    return study_sessions
