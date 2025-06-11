"""AI API endpoints for code generation, explanation, and review."""

import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_ai_service, get_current_user, rate_limiter
from ...core.ai.ai_service import AIService
from ...core.db.database import async_get_db
from ...core.logger import logging
from ...core.utils.ai_monitoring import log_cache_operation
from ...core.utils.cache import client as redis_client
from ...schemas.ai import (
    AIContextResponse,
    AIHealthResponse,
    CodeExplanationRequest,
    CodeExplanationResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeReviewRequest,
    CodeReviewResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


def _generate_code_hash(code: str) -> str:
    """Generate a hash for code content to use as cache key."""
    return hashlib.md5(code.encode()).hexdigest()


async def _get_cached_response(cache_key: str, operation: str = "unknown", user_id: int = None):
    """Get cached response from Redis."""
    if redis_client is None:
        return None
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            log_cache_operation(operation, cache_key, hit=True, user_id=user_id)
            return json.loads(cached_data)
        else:
            log_cache_operation(operation, cache_key, hit=False, user_id=user_id)
    except Exception as e:
        logger.warning(f"Failed to get cached data for key {cache_key}: {e}")
        log_cache_operation(operation, cache_key, hit=False, user_id=user_id)
    return None


async def _set_cached_response(cache_key: str, data: dict, expiration: int):
    """Set cached response in Redis."""
    if redis_client is None:
        return
    try:
        await redis_client.setex(cache_key, expiration, json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Failed to cache data for key {cache_key}: {e}")


@router.post("/generate-code", response_model=CodeGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_code(
    request: Request,
    code_request: CodeGenerationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
) -> CodeGenerationResponse:
    """Generate code from natural language description.

    This endpoint uses AI to generate code based on the provided description,
    programming language, framework, and additional requirements.

    Rate limit: 10 requests per hour per user.
    """
    # Apply rate limiting
    await rate_limiter(request, db, current_user)

    try:
        logger.info(f"User {current_user['id']} requested code generation for: {code_request.description[:100]}...")

        result = await ai_service.generate_code(
            description=code_request.description,
            language=code_request.language,
            framework=code_request.framework,
            additional_requirements=code_request.additional_requirements,
            user_id=current_user['id'],
        )

        response = CodeGenerationResponse(**result)
        logger.info(f"Code generation completed for user {current_user['id']}")
        return response

    except Exception as e:
        logger.error(f"Code generation failed for user {current_user['id']}: {e}")
        if "rate limit" in str(e).lower() or "quota" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service rate limit exceeded. Please try again later."
            )
        elif "timeout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="AI service request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate code. Please try again later."
            )


@router.post("/explain-code", response_model=CodeExplanationResponse, status_code=status.HTTP_200_OK)
async def explain_code(
    request: Request,
    code_request: CodeExplanationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
) -> CodeExplanationResponse:
    """Explain existing code.

    This endpoint uses AI to provide detailed explanations of the provided code,
    with optional focus areas and target audience specification.

    Rate limit: 20 requests per hour per user.
    Caching: Results are cached for 1 hour based on code content hash.
    """
    # Apply rate limiting
    await rate_limiter(request, db, current_user)

    # Generate code hash for caching
    code_hash = _generate_code_hash(code_request.code)
    cache_key = (f"code_explanation:{code_hash}:{code_request.focus_areas or 'none'}:"
                 f"{code_request.target_audience or 'none'}")

    # Check cache first
    cached_response = await _get_cached_response(cache_key, "explain_code", current_user['id'])
    if cached_response:
        logger.info(f"Returning cached code explanation for user {current_user['id']} (hash: {code_hash[:8]}...)")
        return CodeExplanationResponse(**cached_response)

    try:
        logger.info(f"User {current_user['id']} requested code explanation (hash: {code_hash[:8]}...)")

        result = await ai_service.explain_code(
            code=code_request.code,
            focus_areas=code_request.focus_areas,
            target_audience=code_request.target_audience,
            user_id=current_user['id'],
        )

        response = CodeExplanationResponse(**result)

        # Cache the response for 1 hour
        await _set_cached_response(cache_key, result, 3600)

        logger.info(f"Code explanation completed for user {current_user['id']}")
        return response

    except Exception as e:
        logger.error(f"Code explanation failed for user {current_user['id']}: {e}")
        if "rate limit" in str(e).lower() or "quota" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service rate limit exceeded. Please try again later."
            )
        elif "timeout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="AI service request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to explain code. Please try again later."
            )


@router.post("/review-code", response_model=CodeReviewResponse, status_code=status.HTTP_200_OK)
async def review_code(
    request: Request,
    code_request: CodeReviewRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
) -> CodeReviewResponse:
    """Provide code review suggestions.

    This endpoint uses AI to review the provided code and offer suggestions
    for improvements, security issues, performance optimizations, etc.

    Rate limit: 15 requests per hour per user.
    Caching: Results are cached for 30 minutes based on code content hash.
    """
    # Apply rate limiting
    await rate_limiter(request, db, current_user)

    # Generate code hash for caching
    code_hash = _generate_code_hash(code_request.code)
    cache_key = (f"code_review:{code_hash}:{code_request.review_type or 'general'}:"
                 f"{code_request.specific_concerns or 'none'}")

    # Check cache first
    cached_response = await _get_cached_response(cache_key, "review_code", current_user['id'])
    if cached_response:
        logger.info(f"Returning cached code review for user {current_user['id']} (hash: {code_hash[:8]}...)")
        return CodeReviewResponse(**cached_response)

    try:
        logger.info(f"User {current_user['id']} requested code review (hash: {code_hash[:8]}...)")

        result = await ai_service.review_code(
            code=code_request.code,
            review_type=code_request.review_type,
            specific_concerns=code_request.specific_concerns,
            user_id=current_user['id'],
        )

        response = CodeReviewResponse(**result)

        # Cache the response for 30 minutes
        await _set_cached_response(cache_key, result, 1800)

        logger.info(f"Code review completed for user {current_user['id']}")
        return response

    except Exception as e:
        logger.error(f"Code review failed for user {current_user['id']}: {e}")
        if "rate limit" in str(e).lower() or "quota" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service rate limit exceeded. Please try again later."
            )
        elif "timeout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="AI service request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to review code. Please try again later."
            )


@router.get("/health", response_model=AIHealthResponse, status_code=status.HTTP_200_OK)
async def ai_health_check(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
) -> AIHealthResponse:
    """Check AI service health status.

    This endpoint provides information about the current health and status
    of the AI service, including model information and configuration.

    Rate limit: 100 requests per hour per user.
    Caching: Results are cached for 5 minutes.
    """
    # Apply rate limiting
    await rate_limiter(request, db, current_user)

    # Check cache first
    cache_key = "ai_health_check"
    cached_response = await _get_cached_response(cache_key, "health_check", current_user['id'])
    if cached_response:
        logger.info(f"Returning cached AI health check for user {current_user['id']}")
        return AIHealthResponse(**cached_response)

    try:
        logger.info(f"User {current_user['id']} requested AI health check")

        result = await ai_service.health_check()
        response = AIHealthResponse(**result)

        # Cache the response for 5 minutes
        await _set_cached_response(cache_key, result, 300)

        logger.info(f"AI health check completed for user {current_user['id']}: {response.status}")
        return response

    except Exception as e:
        logger.error(f"AI health check failed for user {current_user['id']}: {e}")
        # For health checks, we still want to return a response even if there's an error
        return AIHealthResponse(
            status="unhealthy",
            service="OpenAI",
            model="unknown",
            error=str(e)
        )


@router.get("/context", response_model=AIContextResponse, status_code=status.HTTP_200_OK)
async def get_ai_context(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
) -> AIContextResponse:
    """Get AI service context and configuration.

    This endpoint provides information about the current AI service configuration,
    including model details, limits, and available operations.

    Rate limit: 50 requests per hour per user.
    Caching: Results are cached for 10 minutes.
    """
    # Apply rate limiting
    await rate_limiter(request, db, current_user)

    # Check cache first
    cache_key = "ai_context_info"
    cached_response = await _get_cached_response(cache_key, "context_info", current_user['id'])
    if cached_response:
        logger.info(f"Returning cached AI context information for user {current_user['id']}")
        return AIContextResponse(**cached_response)

    try:
        logger.info(f"User {current_user['id']} requested AI context information")

        result = ai_service.get_context_info()
        response = AIContextResponse(**result)

        # Cache the response for 10 minutes
        await _set_cached_response(cache_key, result, 600)

        logger.info(f"AI context information provided to user {current_user['id']}")
        return response

    except Exception as e:
        logger.error(f"Failed to get AI context for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI context information."
        )
