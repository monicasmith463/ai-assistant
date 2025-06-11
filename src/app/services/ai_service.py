"""AI service for generating questions and explanations using OpenAI."""

import json
from typing import Any

from openai import AsyncOpenAI

from ..core.config import settings
from ..core.logger import logging

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered question generation and explanations."""

    def __init__(self):
        """Initialize AI service with OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS

    async def generate_questions(
        self, content: str, num_questions: int = 5, difficulty: str = "medium"
    ) -> list[dict[str, Any]]:
        """Generate questions from document content using OpenAI.

        Args:
            content: Document text content
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            List of generated questions with answers and explanations

        Raises:
            Exception: If AI generation fails
        """
        try:
            prompt = self._create_question_prompt(content, num_questions, difficulty)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator who creates high-quality study questions. "
                        "Always respond with valid JSON format as specified."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )

            response_content = response.choices[0].message.content
            logger.info(f"Generated questions response: {len(response_content)} characters")

            # Parse the JSON response
            questions_data = json.loads(response_content)

            # Validate and format the response
            formatted_questions = []
            for q in questions_data.get("questions", []):
                formatted_question = {
                    "question_text": q.get("question"),
                    "question_type": q.get("type", "multiple_choice"),
                    "correct_answer": q.get("correct_answer"),
                    "options": json.dumps(q.get("options", [])) if q.get("options") else None,
                    "explanation": q.get("explanation"),
                    "difficulty": difficulty
                }
                formatted_questions.append(formatted_question)

            logger.info(f"Successfully generated {len(formatted_questions)} questions")
            return formatted_questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            raise Exception("AI service returned invalid response format")
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise Exception(f"Failed to generate questions: {str(e)}")

    async def generate_explanation(self, question: str, answer: str) -> str:
        """Generate explanation for a question-answer pair.

        Args:
            question: The question text
            answer: The correct answer

        Returns:
            Generated explanation

        Raises:
            Exception: If explanation generation fails
        """
        try:
            prompt = f"""
            Please provide a clear and educational explanation for why the following answer is correct:

            Question: {question}
            Correct Answer: {answer}

            Provide a concise but thorough explanation that helps a student understand the concept.
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator who provides clear, helpful explanations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.5,
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated explanation: {len(explanation)} characters")
            return explanation

        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise Exception(f"Failed to generate explanation: {str(e)}")

    def _create_question_prompt(self, content: str, num_questions: int, difficulty: str) -> str:
        """Create prompt for question generation.

        Args:
            content: Document content
            num_questions: Number of questions to generate
            difficulty: Difficulty level

        Returns:
            Formatted prompt for AI
        """
        difficulty_instructions = {
            "easy": "Focus on basic facts, definitions, and simple recall questions.",
            "medium": "Include application questions and moderate analysis of concepts.",
            "hard": "Create complex analysis, synthesis, and evaluation questions."
        }

        instruction = difficulty_instructions.get(difficulty, difficulty_instructions["medium"])

        prompt = f"""
        Based on the following document content, generate {num_questions} study questions at {difficulty} difficulty level.
        {instruction}

        Document Content:
        {content[:3000]}  # Limit content to avoid token limits

        Please generate questions in the following JSON format:
        {{
            "questions": [
                {{
                    "question": "Question text here?",
                    "type": "multiple_choice",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Explanation of why this answer is correct"
                }},
                {{
                    "question": "Another question?",
                    "type": "short_answer",
                    "correct_answer": "Expected answer",
                    "explanation": "Explanation of the answer"
                }}
            ]
        }}

        Question types can be: "multiple_choice", "short_answer", or "true_false"
        For multiple_choice questions, provide 4 options.
        For true_false questions, correct_answer should be "True" or "False".
        Always include explanations.
        """

        return prompt

    async def validate_api_key(self) -> bool:
        """Validate that the OpenAI API key is working.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False
