"""Tests for AI service."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from src.app.services.ai_service import AIService


class TestAIService:
    """Test cases for AIService."""

    @pytest.fixture
    def ai_service(self):
        """Create AIService instance for testing."""
        with patch('src.app.services.ai_service.AsyncOpenAI'):
            return AIService()

    @pytest.mark.asyncio
    async def test_generate_questions_success(self, ai_service):
        """Test successful question generation."""
        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = json.dumps({
            "questions": [
                {
                    "question": "What is the main topic?",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "This is correct because..."
                },
                {
                    "question": "True or false question?",
                    "type": "true_false",
                    "correct_answer": "True",
                    "explanation": "This is true because..."
                }
            ]
        })
        
        ai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await ai_service.generate_questions("Sample content", 2, "medium")
        
        assert len(result) == 2
        assert result[0]["question_text"] == "What is the main topic?"
        assert result[0]["question_type"] == "multiple_choice"
        assert result[0]["correct_answer"] == "A"
        assert result[0]["difficulty"] == "medium"
        assert json.loads(result[0]["options"]) == ["A", "B", "C", "D"]

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_json(self, ai_service):
        """Test question generation with invalid JSON response."""
        # Mock OpenAI response with invalid JSON
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        ai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with pytest.raises(Exception, match="AI service returned invalid response format"):
            await ai_service.generate_questions("Sample content", 2, "medium")

    @pytest.mark.asyncio
    async def test_generate_questions_api_error(self, ai_service):
        """Test question generation with API error."""
        ai_service.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception, match="Failed to generate questions"):
            await ai_service.generate_questions("Sample content", 2, "medium")

    @pytest.mark.asyncio
    async def test_generate_explanation_success(self, ai_service):
        """Test successful explanation generation."""
        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "This is a detailed explanation."
        
        ai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await ai_service.generate_explanation("What is AI?", "Artificial Intelligence")
        
        assert result == "This is a detailed explanation."

    @pytest.mark.asyncio
    async def test_generate_explanation_api_error(self, ai_service):
        """Test explanation generation with API error."""
        ai_service.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception, match="Failed to generate explanation"):
            await ai_service.generate_explanation("What is AI?", "Artificial Intelligence")

    def test_create_question_prompt_easy(self, ai_service):
        """Test prompt creation for easy difficulty."""
        prompt = ai_service._create_question_prompt("Sample content", 5, "easy")
        
        assert "5 study questions" in prompt
        assert "easy difficulty" in prompt
        assert "basic facts, definitions" in prompt
        assert "Sample content" in prompt

    def test_create_question_prompt_medium(self, ai_service):
        """Test prompt creation for medium difficulty."""
        prompt = ai_service._create_question_prompt("Sample content", 3, "medium")
        
        assert "3 study questions" in prompt
        assert "medium difficulty" in prompt
        assert "application questions" in prompt

    def test_create_question_prompt_hard(self, ai_service):
        """Test prompt creation for hard difficulty."""
        prompt = ai_service._create_question_prompt("Sample content", 2, "hard")
        
        assert "2 study questions" in prompt
        assert "hard difficulty" in prompt
        assert "complex analysis" in prompt

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, ai_service):
        """Test successful API key validation."""
        # Mock successful response
        mock_response = AsyncMock()
        ai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await ai_service.validate_api_key()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, ai_service):
        """Test API key validation failure."""
        ai_service.client.chat.completions.create = AsyncMock(side_effect=Exception("Invalid API key"))
        
        result = await ai_service.validate_api_key()
        assert result is False