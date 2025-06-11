"""Pydantic schemas for AI-related operations."""

from typing import Optional

from pydantic import BaseModel, Field


class AIMetadata(BaseModel):
    """Metadata for AI operations."""

    input_tokens: int = Field(..., description="Number of input tokens used")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    total_tokens: int = Field(..., description="Total tokens used")
    model: str = Field(..., description="AI model used for the operation")


class CodeGenerationRequest(BaseModel):
    """Request schema for code generation."""

    description: str = Field(
        ...,
        description="Description of what code to generate",
        min_length=10,
        max_length=2000,
        examples=["Create a Python function that calculates the factorial of a number"]
    )
    language: Optional[str] = Field(
        None,
        description="Programming language for the generated code",
        examples=["Python", "JavaScript", "Java", "C++"]
    )
    framework: Optional[str] = Field(
        None,
        description="Framework to use for the generated code",
        examples=["FastAPI", "React", "Spring Boot", "Django"]
    )
    additional_requirements: Optional[str] = Field(
        None,
        description="Additional requirements or constraints",
        max_length=1000,
        examples=["Include error handling and type hints"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Create a REST API endpoint for user authentication",
                "language": "Python",
                "framework": "FastAPI",
                "additional_requirements": "Include JWT token generation and validation"
            }
        }


class CodeGenerationResponse(BaseModel):
    """Response schema for code generation."""

    generated_code: str = Field(..., description="The generated code")
    language: Optional[str] = Field(None, description="Programming language used")
    framework: Optional[str] = Field(None, description="Framework used")
    description: str = Field(..., description="Original description provided")
    metadata: AIMetadata = Field(..., description="Metadata about the AI operation")

    class Config:
        json_schema_extra = {
            "example": {
                "generated_code": ("def factorial(n):\n    if n <= 1:\n        return 1\n"
                                  "    return n * factorial(n - 1)"),
                "language": "Python",
                "framework": None,
                "description": "Create a Python function that calculates the factorial of a number",
                "metadata": {
                    "input_tokens": 45,
                    "output_tokens": 32,
                    "total_tokens": 77,
                    "model": "gpt-3.5-turbo"
                }
            }
        }


class CodeExplanationRequest(BaseModel):
    """Request schema for code explanation."""

    code: str = Field(
        ...,
        description="Code to explain",
        min_length=10,
        max_length=10000,
        examples=["def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"]
    )
    focus_areas: Optional[str] = Field(
        None,
        description="Specific areas to focus the explanation on",
        max_length=500,
        examples=["recursion", "error handling", "performance"]
    )
    target_audience: Optional[str] = Field(
        None,
        description="Target audience for the explanation",
        examples=["beginner", "intermediate", "advanced", "non-technical"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                "focus_areas": "recursion and base case",
                "target_audience": "beginner"
            }
        }


class CodeExplanationResponse(BaseModel):
    """Response schema for code explanation."""

    explanation: str = Field(..., description="Detailed explanation of the code")
    original_code: str = Field(..., description="The original code that was explained")
    focus_areas: Optional[str] = Field(None, description="Areas that were focused on")
    target_audience: Optional[str] = Field(None, description="Target audience for the explanation")
    metadata: AIMetadata = Field(..., description="Metadata about the AI operation")

    class Config:
        json_schema_extra = {
            "example": {
                "explanation": "This function calculates the factorial of a number using recursion...",
                "original_code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                "focus_areas": "recursion and base case",
                "target_audience": "beginner",
                "metadata": {
                    "input_tokens": 65,
                    "output_tokens": 150,
                    "total_tokens": 215,
                    "model": "gpt-3.5-turbo"
                }
            }
        }


class CodeReviewRequest(BaseModel):
    """Request schema for code review."""

    code: str = Field(
        ...,
        description="Code to review",
        min_length=10,
        max_length=10000,
        examples=["def simple_function(): pass"]
    )
    review_type: Optional[str] = Field(
        None,
        description="Type of review to focus on",
        examples=["security", "performance", "best_practices", "general"]
    )
    specific_concerns: Optional[str] = Field(
        None,
        description="Specific concerns or areas to focus the review on",
        max_length=500,
        examples=["potential security vulnerabilities", "performance bottlenecks"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def process_data(data):\n    return [item * 2 for item in data]",
                "review_type": "performance",
                "specific_concerns": "efficiency of the loop and memory usage"
            }
        }


class CodeReviewResponse(BaseModel):
    """Response schema for code review."""

    review: str = Field(..., description="Detailed code review with recommendations")
    original_code: str = Field(..., description="The original code that was reviewed")
    review_type: Optional[str] = Field(None, description="Type of review that was performed")
    specific_concerns: Optional[str] = Field(None, description="Specific concerns that were addressed")
    metadata: AIMetadata = Field(..., description="Metadata about the AI operation")

    class Config:
        json_schema_extra = {
            "example": {
                "review": "The code can be improved for performance by using list comprehension...",
                "original_code": "def process_data(data):\n    return [item * 2 for item in data]",
                "review_type": "performance",
                "specific_concerns": "efficiency of the loop and memory usage",
                "metadata": {
                    "input_tokens": 85,
                    "output_tokens": 200,
                    "total_tokens": 285,
                    "model": "gpt-3.5-turbo"
                }
            }
        }


class AIHealthResponse(BaseModel):
    """Response schema for AI service health check."""

    status: str = Field(..., description="Health status of the AI service")
    service: str = Field(..., description="Name of the AI service")
    model: str = Field(..., description="AI model being used")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens per request")
    temperature: Optional[float] = Field(None, description="Temperature setting")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "OpenAI",
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.7,
                "timeout": 30
            }
        }


class AIContextResponse(BaseModel):
    """Response schema for AI service context information."""

    model: str = Field(..., description="AI model being used")
    max_tokens: int = Field(..., description="Maximum tokens per request")
    temperature: float = Field(..., description="Temperature setting")
    timeout: int = Field(..., description="Request timeout in seconds")
    available_operations: list[str] = Field(..., description="List of available AI operations")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.7,
                "timeout": 30,
                "available_operations": ["generate_code", "explain_code", "review_code"]
            }
        }
