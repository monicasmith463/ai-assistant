"""AI module for the FastAPI application."""

from .ai_service import AIService
from .llm_client import OpenAIClient
from .prompt_templates import (
    CodeExplanationTemplate,
    CodeGenerationTemplate,
    CodeReviewTemplate,
    PromptTemplate,
)

__all__ = [
    "AIService",
    "OpenAIClient",
    "PromptTemplate",
    "CodeGenerationTemplate",
    "CodeExplanationTemplate",
    "CodeReviewTemplate",
]
