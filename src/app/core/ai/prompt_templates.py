"""Prompt templates for different AI tasks."""

from abc import ABC, abstractmethod
from typing import Optional


class PromptTemplate(ABC):
    """Base class for prompt templates."""

    @abstractmethod
    def format(self, **kwargs) -> dict[str, str]:
        """Format the template with provided arguments.

        Returns:
            Dictionary with 'system' and 'user' messages
        """
        pass


class CodeGenerationTemplate(PromptTemplate):
    """Template for code generation tasks."""

    def format(
        self,
        description: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        additional_requirements: Optional[str] = None,
        **kwargs
    ) -> dict[str, str]:
        """Format the code generation template.

        Args:
            description: Description of what code to generate
            language: Programming language (optional)
            framework: Framework to use (optional)
            additional_requirements: Additional requirements (optional)

        Returns:
            Formatted prompt messages
        """
        system_message = (
            "You are an expert software developer and code generator. "
            "Your task is to generate high-quality, production-ready code based on user requirements.\n\n"
            "Guidelines:\n"
            "- Write clean, readable, and well-documented code\n"
            "- Follow best practices and conventions for the specified language/framework\n"
            "- Include proper error handling where appropriate\n"
            "- Add helpful comments to explain complex logic\n"
            "- Ensure code is secure and follows security best practices\n"
            "- Make the code modular and maintainable\n\n"
            "Format your response with:\n"
            "1. Brief explanation of the approach\n"
            "2. The complete code implementation\n"
            "3. Usage examples if applicable\n"
            "4. Any important notes or considerations"
        )

        user_prompt = f"Generate code for the following requirement:\n\n{description}"

        if language:
            user_prompt += f"\n\nProgramming Language: {language}"

        if framework:
            user_prompt += f"\nFramework: {framework}"

        if additional_requirements:
            user_prompt += f"\nAdditional Requirements: {additional_requirements}"

        return {
            "system": system_message,
            "user": user_prompt
        }


class CodeExplanationTemplate(PromptTemplate):
    """Template for code explanation tasks."""

    def format(
        self,
        code: str,
        focus_areas: Optional[str] = None,
        target_audience: Optional[str] = None,
        **kwargs
    ) -> dict[str, str]:
        """Format the code explanation template.

        Args:
            code: Code to explain
            focus_areas: Specific areas to focus on (optional)
            target_audience: Target audience level (optional)

        Returns:
            Formatted prompt messages
        """
        system_message = (
            "You are an expert software engineer and technical educator. "
            "Your task is to explain code in a clear, comprehensive, and educational manner.\n\n"
            "Guidelines:\n"
            "- Provide clear explanations that are appropriate for the target audience\n"
            "- Break down complex concepts into understandable parts\n"
            "- Explain the purpose and functionality of each major component\n"
            "- Highlight important patterns, best practices, or potential issues\n"
            "- Use examples and analogies when helpful\n"
            "- Structure your explanation logically from high-level overview to details\n\n"
            "Format your response with:\n"
            "1. High-level overview of what the code does\n"
            "2. Step-by-step breakdown of the logic\n"
            "3. Explanation of key concepts or patterns used\n"
            "4. Potential improvements or considerations\n"
            "5. Summary of key takeaways"
        )

        user_prompt = f"Please explain the following code:\n\n```\n{code}\n```"

        if target_audience:
            user_prompt += f"\n\nTarget Audience: {target_audience}"

        if focus_areas:
            user_prompt += f"\nFocus Areas: {focus_areas}"

        return {
            "system": system_message,
            "user": user_prompt
        }


class CodeReviewTemplate(PromptTemplate):
    """Template for code review tasks."""

    def format(
        self,
        code: str,
        review_type: Optional[str] = None,
        specific_concerns: Optional[str] = None,
        **kwargs
    ) -> dict[str, str]:
        """Format the code review template.

        Args:
            code: Code to review
            review_type: Type of review (security, performance, general, etc.)
            specific_concerns: Specific areas of concern (optional)

        Returns:
            Formatted prompt messages
        """
        system_message = (
            "You are an expert software developer and code reviewer. "
            "Your task is to provide thorough, constructive code reviews that help improve "
            "code quality, security, and maintainability.\n\n"
            "Guidelines:\n"
            "- Provide specific, actionable feedback\n"
            "- Point out both positive aspects and areas for improvement\n"
            "- Consider security, performance, readability, and maintainability\n"
            "- Suggest concrete improvements with examples when possible\n"
            "- Prioritize feedback by importance (critical, important, nice-to-have)\n"
            "- Be constructive and educational in your tone\n\n"
            "Format your response with:\n"
            "1. Overall assessment summary\n"
            "2. Critical issues (security, bugs)\n"
            "3. Important improvements (performance, maintainability)\n"
            "4. Code quality suggestions (style, readability)\n"
            "5. Positive aspects worth highlighting"
        )

        user_prompt = f"Please review the following code:\n\n```\n{code}\n```"

        if review_type:
            user_prompt += f"\n\nReview Type: {review_type}"

        if specific_concerns:
            user_prompt += f"\nSpecific Concerns: {specific_concerns}"

        return {
            "system": system_message,
            "user": user_prompt
        }


class CustomPromptTemplate(PromptTemplate):
    """Template for custom prompts with flexible system and user messages."""

    def __init__(self, system_template: str, user_template: str):
        """Initialize with custom templates.

        Args:
            system_template: System message template with placeholders
            user_template: User message template with placeholders
        """
        self.system_template = system_template
        self.user_template = user_template

    def format(self, **kwargs) -> dict[str, str]:
        """Format the custom template with provided arguments.

        Returns:
            Formatted prompt messages
        """
        return {
            "system": self.system_template.format(**kwargs),
            "user": self.user_template.format(**kwargs)
        }
