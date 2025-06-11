"""Main AI service that orchestrates AI operations."""

import asyncio
import logging
from typing import Optional

from ..utils.ai_monitoring import log_token_usage, monitor_ai_operation
from .llm_client import OpenAIClient
from .prompt_templates import (
    CodeExplanationTemplate,
    CodeGenerationTemplate,
    CodeReviewTemplate,
)

logger = logging.getLogger(__name__)


class AIService:
    """Main AI service class that orchestrates AI operations."""

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """Initialize the AI service.

        Args:
            openai_client: OpenAI client instance. If not provided, creates a new one.
        """
        self.client = openai_client or OpenAIClient()
        self.code_generation_template = CodeGenerationTemplate()
        self.code_explanation_template = CodeExplanationTemplate()
        self.code_review_template = CodeReviewTemplate()

    async def _retry_with_backoff(self, operation, max_retries: int = 3, base_delay: float = 1.0):
        """Retry an operation with exponential backoff.

        Args:
            operation: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds

        Returns:
            Result of the operation

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_exception = e

                # Check if this is a retryable error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ["rate limit", "quota", "timeout", "network", "connection"]):
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Retryable error on attempt {attempt + 1}: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue

                # Non-retryable error, raise immediately
                raise e

        # All retries exhausted
        raise last_exception

    async def generate_code(
        self,
        description: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        additional_requirements: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> dict[str, any]:
        """Generate code based on description and requirements.

        Args:
            description: Description of what code to generate
            language: Programming language (optional)
            framework: Framework to use (optional)
            additional_requirements: Additional requirements (optional)
            user_id: User ID for monitoring (optional)
            **kwargs: Additional parameters for the AI call

        Returns:
            Dictionary containing generated code and metadata
        """
        async with monitor_ai_operation("generate_code", user_id, self.client.model) as op_data:
            try:
                # Format the prompt
                prompt_data = self.code_generation_template.format(
                    description=description,
                    language=language,
                    framework=framework,
                    additional_requirements=additional_requirements
                )

                # Define the operation to retry
                async def _generate():
                    return await self.client.generate_text(
                        prompt=prompt_data["user"],
                        system_message=prompt_data["system"],
                        **kwargs
                    )

                # Execute with retry logic
                response = await self._retry_with_backoff(_generate)

                # Count tokens for metadata
                input_tokens = self.client.count_tokens(
                    prompt_data["system"] + prompt_data["user"]
                )
                output_tokens = self.client.count_tokens(response)
                total_tokens = input_tokens + output_tokens

                # Update operation data for monitoring
                op_data["input_tokens"] = input_tokens
                op_data["output_tokens"] = output_tokens
                op_data["total_tokens"] = total_tokens

                # Log token usage
                log_token_usage("generate_code", user_id, input_tokens, output_tokens, self.client.model)

                return {
                    "generated_code": response,
                    "language": language,
                    "framework": framework,
                    "description": description,
                    "metadata": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                        "model": self.client.model
                    }
                }

            except Exception as e:
                logger.error(f"Code generation failed: {e}")
                # Determine appropriate error message based on error type
                error_str = str(e).lower()
                if "rate limit" in error_str or "quota" in error_str:
                    raise Exception("AI service rate limit exceeded. Please try again later.")
                elif "timeout" in error_str:
                    raise Exception("AI service request timed out. Please try again.")
                elif "authentication" in error_str or "api key" in error_str:
                    raise Exception("AI service authentication failed. Please check configuration.")
                else:
                    raise Exception(f"Failed to generate code: {str(e)}")

    async def explain_code(
        self,
        code: str,
        focus_areas: Optional[str] = None,
        target_audience: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> dict[str, any]:
        """Explain the provided code.

        Args:
            code: Code to explain
            focus_areas: Specific areas to focus on (optional)
            target_audience: Target audience level (optional)
            user_id: User ID for monitoring (optional)
            **kwargs: Additional parameters for the AI call

        Returns:
            Dictionary containing code explanation and metadata
        """
        async with monitor_ai_operation("explain_code", user_id, self.client.model) as op_data:
            try:
                # Format the prompt
                prompt_data = self.code_explanation_template.format(
                    code=code,
                    focus_areas=focus_areas,
                    target_audience=target_audience
                )

                # Define the operation to retry
                async def _explain():
                    return await self.client.generate_text(
                        prompt=prompt_data["user"],
                        system_message=prompt_data["system"],
                        **kwargs
                    )

                # Execute with retry logic
                response = await self._retry_with_backoff(_explain)

                # Count tokens for metadata
                input_tokens = self.client.count_tokens(
                    prompt_data["system"] + prompt_data["user"]
                )
                output_tokens = self.client.count_tokens(response)
                total_tokens = input_tokens + output_tokens

                # Update operation data for monitoring
                op_data["input_tokens"] = input_tokens
                op_data["output_tokens"] = output_tokens
                op_data["total_tokens"] = total_tokens

                # Log token usage
                log_token_usage("explain_code", user_id, input_tokens, output_tokens, self.client.model)

                return {
                    "explanation": response,
                    "original_code": code,
                    "focus_areas": focus_areas,
                    "target_audience": target_audience,
                    "metadata": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                        "model": self.client.model
                    }
                }

            except Exception as e:
                logger.error(f"Code explanation failed: {e}")
                # Determine appropriate error message based on error type
                error_str = str(e).lower()
                if "rate limit" in error_str or "quota" in error_str:
                    raise Exception("AI service rate limit exceeded. Please try again later.")
                elif "timeout" in error_str:
                    raise Exception("AI service request timed out. Please try again.")
                elif "authentication" in error_str or "api key" in error_str:
                    raise Exception("AI service authentication failed. Please check configuration.")
                else:
                    raise Exception(f"Failed to explain code: {str(e)}")

    async def review_code(
        self,
        code: str,
        review_type: Optional[str] = None,
        specific_concerns: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> dict[str, any]:
        """Review the provided code.

        Args:
            code: Code to review
            review_type: Type of review (security, performance, general, etc.)
            specific_concerns: Specific areas of concern (optional)
            user_id: User ID for monitoring (optional)
            **kwargs: Additional parameters for the AI call

        Returns:
            Dictionary containing code review and metadata
        """
        async with monitor_ai_operation("review_code", user_id, self.client.model) as op_data:
            try:
                # Format the prompt
                prompt_data = self.code_review_template.format(
                    code=code,
                    review_type=review_type,
                    specific_concerns=specific_concerns
                )

                # Define the operation to retry
                async def _review():
                    return await self.client.generate_text(
                        prompt=prompt_data["user"],
                        system_message=prompt_data["system"],
                        **kwargs
                    )

                # Execute with retry logic
                response = await self._retry_with_backoff(_review)

                # Count tokens for metadata
                input_tokens = self.client.count_tokens(
                    prompt_data["system"] + prompt_data["user"]
                )
                output_tokens = self.client.count_tokens(response)
                total_tokens = input_tokens + output_tokens

                # Update operation data for monitoring
                op_data["input_tokens"] = input_tokens
                op_data["output_tokens"] = output_tokens
                op_data["total_tokens"] = total_tokens

                # Log token usage
                log_token_usage("review_code", user_id, input_tokens, output_tokens, self.client.model)

                return {
                    "review": response,
                    "original_code": code,
                    "review_type": review_type,
                    "specific_concerns": specific_concerns,
                    "metadata": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                        "model": self.client.model
                    }
                }

            except Exception as e:
                logger.error(f"Code review failed: {e}")
                # Determine appropriate error message based on error type
                error_str = str(e).lower()
                if "rate limit" in error_str or "quota" in error_str:
                    raise Exception("AI service rate limit exceeded. Please try again later.")
                elif "timeout" in error_str:
                    raise Exception("AI service request timed out. Please try again.")
                elif "authentication" in error_str or "api key" in error_str:
                    raise Exception("AI service authentication failed. Please check configuration.")
                else:
                    raise Exception(f"Failed to review code: {str(e)}")

    async def health_check(self) -> dict[str, any]:
        """Check the health of the AI service.

        Returns:
            Dictionary containing health status and service information
        """
        try:
            is_healthy = await self.client.health_check()

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "OpenAI",
                "model": self.client.model,
                "max_tokens": self.client.max_tokens,
                "temperature": self.client.temperature,
                "timeout": self.client.timeout
            }

        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "OpenAI",
                "model": self.client.model
            }

    def get_context_info(self) -> dict[str, any]:
        """Get information about the current AI service context.

        Returns:
            Dictionary containing context information
        """
        return {
            "model": self.client.model,
            "max_tokens": self.client.max_tokens,
            "temperature": self.client.temperature,
            "timeout": self.client.timeout,
            "available_operations": [
                "generate_code",
                "explain_code",
                "review_code"
            ]
        }
