"""Tests for questions API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.app.main import app
from tests.conftest import override_dependency
from src.app.api.dependencies import get_current_user
from src.app.core.db.database import async_get_db


class TestQuestionsAPI:
    """Test cases for questions API endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return {"id": 1, "username": "testuser", "email": "test@example.com"}

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client_with_auth(self, mock_user, mock_db):
        """Test client with mocked authentication."""
        override_dependency(get_current_user, mock_user)
        override_dependency(async_get_db, mock_db)
        return TestClient(app)

    def test_generate_questions_success(self, client_with_auth, mock_db):
        """Test successful question generation."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get_doc, \
             patch('src.app.services.ai_service.AIService.generate_questions') as mock_generate, \
             patch('src.app.crud.crud_questions.crud_questions.create') as mock_create:
            
            # Mock document
            mock_get_doc.return_value = {
                "id": 1,
                "content": "Sample document content for question generation"
            }
            
            # Mock AI service response
            mock_generate.return_value = [
                {
                    "question_text": "What is the main topic?",
                    "question_type": "multiple_choice",
                    "correct_answer": "A",
                    "options": '["A", "B", "C", "D"]',
                    "explanation": "This is correct because...",
                    "difficulty": "medium"
                }
            ]
            
            # Mock question creation
            mock_create.return_value = {
                "id": 1,
                "question_text": "What is the main topic?",
                "question_type": "multiple_choice",
                "correct_answer": "A",
                "options": '["A", "B", "C", "D"]',
                "explanation": "This is correct because...",
                "difficulty": "medium",
                "document_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None
            }
            
            response = client_with_auth.post("/api/v1/questions/generate/1?num_questions=1&difficulty=medium")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["question_text"] == "What is the main topic?"

    def test_generate_questions_document_not_found(self, client_with_auth, mock_db):
        """Test question generation with non-existent document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get_doc:
            mock_get_doc.return_value = None
            
            response = client_with_auth.post("/api/v1/questions/generate/999")
            
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]

    def test_generate_questions_no_content(self, client_with_auth, mock_db):
        """Test question generation with document having no content."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get_doc:
            mock_get_doc.return_value = {"id": 1, "content": None}
            
            response = client_with_auth.post("/api/v1/questions/generate/1")
            
            assert response.status_code == 400
            assert "no extractable content" in response.json()["detail"]

    def test_generate_questions_ai_service_error(self, client_with_auth, mock_db):
        """Test question generation with AI service error."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get_doc, \
             patch('src.app.services.ai_service.AIService.generate_questions') as mock_generate:
            
            mock_get_doc.return_value = {"id": 1, "content": "Sample content"}
            mock_generate.side_effect = Exception("AI service error")
            
            response = client_with_auth.post("/api/v1/questions/generate/1")
            
            assert response.status_code == 500
            assert "Question generation failed" in response.json()["detail"]

    def test_get_questions_for_document_success(self, client_with_auth, mock_db):
        """Test getting questions for a document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get_doc, \
             patch('src.app.crud.crud_questions.crud_questions.get_multi') as mock_get_questions:
            
            mock_get_doc.return_value = {"id": 1}
            mock_get_questions.return_value = [
                {
                    "id": 1,
                    "question_text": "Question 1?",
                    "question_type": "multiple_choice",
                    "correct_answer": "A",
                    "options": '["A", "B", "C", "D"]',
                    "explanation": "Explanation 1",
                    "difficulty": "medium",
                    "document_id": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None
                },
                {
                    "id": 2,
                    "question_text": "Question 2?",
                    "question_type": "short_answer",
                    "correct_answer": "Answer 2",
                    "options": None,
                    "explanation": "Explanation 2",
                    "difficulty": "easy",
                    "document_id": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None
                }
            ]
            
            response = client_with_auth.get("/api/v1/questions/document/1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["question_text"] == "Question 1?"
            assert data[1]["question_text"] == "Question 2?"

    def test_get_question_success(self, client_with_auth, mock_db):
        """Test getting a specific question."""
        with patch('src.app.crud.crud_questions.crud_questions.get') as mock_get:
            mock_get.return_value = {
                "id": 1,
                "question_text": "What is AI?",
                "question_type": "short_answer",
                "correct_answer": "Artificial Intelligence",
                "options": None,
                "explanation": "AI stands for Artificial Intelligence",
                "difficulty": "easy",
                "document_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None
            }
            
            response = client_with_auth.get("/api/v1/questions/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["question_text"] == "What is AI?"

    def test_get_question_not_found(self, client_with_auth, mock_db):
        """Test getting a non-existent question."""
        with patch('src.app.crud.crud_questions.crud_questions.get') as mock_get:
            mock_get.return_value = None
            
            response = client_with_auth.get("/api/v1/questions/999")
            
            assert response.status_code == 404
            assert "Question not found" in response.json()["detail"]

    def test_delete_question_success(self, client_with_auth, mock_db):
        """Test deleting a question."""
        with patch('src.app.crud.crud_questions.crud_questions.get') as mock_get, \
             patch('src.app.crud.crud_questions.crud_questions.db_delete') as mock_delete:
            
            mock_get.return_value = {"id": 1}
            mock_delete.return_value = None
            
            response = client_with_auth.delete("/api/v1/questions/1")
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]

    def test_regenerate_explanation_success(self, client_with_auth, mock_db):
        """Test regenerating explanation for a question."""
        with patch('src.app.crud.crud_questions.crud_questions.get') as mock_get, \
             patch('src.app.services.ai_service.AIService.generate_explanation') as mock_generate, \
             patch('src.app.crud.crud_questions.crud_questions.update') as mock_update:
            
            mock_get.return_value = {
                "id": 1,
                "question_text": "What is AI?",
                "correct_answer": "Artificial Intelligence"
            }
            mock_generate.return_value = "New detailed explanation about AI"
            mock_update.return_value = {
                "id": 1,
                "question_text": "What is AI?",
                "question_type": "short_answer",
                "correct_answer": "Artificial Intelligence",
                "options": None,
                "explanation": "New detailed explanation about AI",
                "difficulty": "easy",
                "document_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T01:00:00Z"
            }
            
            response = client_with_auth.post("/api/v1/questions/regenerate-explanation/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["explanation"] == "New detailed explanation about AI"

    def test_invalid_query_parameters(self, client_with_auth, mock_db):
        """Test question generation with invalid query parameters."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get_doc:
            mock_get_doc.return_value = {"id": 1, "content": "Sample content"}
            
            # Test invalid num_questions
            response = client_with_auth.post("/api/v1/questions/generate/1?num_questions=25")
            assert response.status_code == 422
            
            # Test invalid difficulty
            response = client_with_auth.post("/api/v1/questions/generate/1?difficulty=invalid")
            assert response.status_code == 422