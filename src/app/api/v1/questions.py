"""API endpoints for question management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user, rate_limiter
from ...core.db.database import async_get_db
from ...crud.crud_documents import crud_documents
from ...crud.crud_questions import crud_questions
from ...schemas.question import QuestionCreateInternal, QuestionRead
from ...services.ai_service import AIService

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/generate/{document_id}", response_model=list[QuestionRead], dependencies=[Depends(rate_limiter)])
async def generate_questions(
    document_id: int,
    num_questions: Annotated[int, Query(ge=1, le=20)] = 5,
    difficulty: Annotated[str, Query(regex="^(easy|medium|hard)$")] = "medium",
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Generate questions from a document.

    Args:
        document_id: ID of the document to generate questions from
        num_questions: Number of questions to generate (1-20)
        difficulty: Difficulty level (easy, medium, hard)
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of generated questions

    Raises:
        HTTPException: If document not found, access denied, or generation fails
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

    if not document.get("content"):
        raise HTTPException(status_code=400, detail="Document has no extractable content")

    try:
        # Generate questions using AI service
        ai_service = AIService()
        generated_questions = await ai_service.generate_questions(
            content=document["content"],
            num_questions=num_questions,
            difficulty=difficulty
        )

        # Save questions to database
        saved_questions = []
        for question_data in generated_questions:
            question_create = QuestionCreateInternal(
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                correct_answer=question_data["correct_answer"],
                options=question_data.get("options"),
                explanation=question_data.get("explanation"),
                difficulty=question_data["difficulty"],
                document_id=document_id,
                user_id=current_user["id"]
            )

            saved_question = await crud_questions.create(session, object=question_create)
            saved_questions.append(saved_question)

        return saved_questions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.get("/document/{document_id}", response_model=list[QuestionRead])
async def get_questions_for_document(
    document_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get all questions for a document.

    Args:
        document_id: ID of the document
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of questions for the document

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

    # Get questions for the document
    questions = await crud_questions.get_multi(
        session,
        document_id=document_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    return questions


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question(
    question_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Get a specific question.

    Args:
        question_id: ID of the question
        current_user: Current authenticated user
        session: Database session

    Returns:
        Question information

    Raises:
        HTTPException: If question not found or access denied
    """
    question = await crud_questions.get(
        session,
        id=question_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return question


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Delete a question.

    Args:
        question_id: ID of the question to delete
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If question not found or access denied
    """
    # Check if question exists and belongs to user
    question = await crud_questions.get(
        session,
        id=question_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Soft delete the question
    await crud_questions.db_delete(session, id=question_id)

    return {"message": "Question deleted successfully"}


@router.post("/regenerate-explanation/{question_id}", response_model=QuestionRead, dependencies=[Depends(rate_limiter)])
async def regenerate_explanation(
    question_id: int,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(async_get_db)
):
    """Regenerate explanation for a question.

    Args:
        question_id: ID of the question
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated question with new explanation

    Raises:
        HTTPException: If question not found, access denied, or generation fails
    """
    # Check if question exists and belongs to user
    question = await crud_questions.get(
        session,
        id=question_id,
        user_id=current_user["id"],
        is_deleted=False
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        # Generate new explanation
        ai_service = AIService()
        new_explanation = await ai_service.generate_explanation(
            question=question["question_text"],
            answer=question["correct_answer"]
        )

        # Update question with new explanation
        from datetime import UTC, datetime

        from ...schemas.question import QuestionUpdateInternal

        update_data = QuestionUpdateInternal(
            explanation=new_explanation,
            updated_at=datetime.now(UTC)
        )

        updated_question = await crud_questions.update(session, object=update_data, id=question_id)
        return updated_question

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")
