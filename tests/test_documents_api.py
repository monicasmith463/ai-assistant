"""Tests for documents API endpoints."""

import io
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import UploadFile

from src.app.main import app
from tests.conftest import override_dependency
from src.app.api.dependencies import get_current_user
from src.app.core.db.database import async_get_db


class TestDocumentsAPI:
    """Test cases for documents API endpoints."""

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

    def test_upload_document_success(self, client_with_auth, mock_db):
        """Test successful document upload."""
        # Mock file upload and processing
        with patch('src.app.services.file_upload.FileUploadService.save_uploaded_file') as mock_save, \
             patch('src.app.services.file_upload.FileUploadService.get_file_size') as mock_size, \
             patch('src.app.services.file_upload.FileUploadService.get_file_content') as mock_content, \
             patch('src.app.services.document_processor.DocumentProcessor.process_document') as mock_process, \
             patch('src.app.crud.crud_documents.crud_documents.create') as mock_create:
            
            mock_save.return_value = ("/path/to/file.pdf", "test.pdf")
            mock_size.return_value = 1024
            mock_content.return_value = b"file content"
            mock_process.return_value = "Extracted text content"
            mock_create.return_value = {
                "id": 1,
                "title": "test",
                "filename": "test.pdf",
                "file_type": "pdf",
                "file_size": 1024,
                "content": "Extracted text content",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None
            }
            
            # Create test file
            test_file = io.BytesIO(b"test pdf content")
            files = {"file": ("test.pdf", test_file, "application/pdf")}
            
            response = client_with_auth.post("/api/v1/documents/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "test"
            assert data["filename"] == "test.pdf"
            assert data["file_type"] == "pdf"

    def test_upload_document_invalid_file_type(self, client_with_auth):
        """Test document upload with invalid file type."""
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.txt", test_file, "text/plain")}
        
        with patch('src.app.services.file_upload.FileUploadService.validate_file') as mock_validate:
            mock_validate.side_effect = Exception("File type 'txt' not allowed")
            
            response = client_with_auth.post("/api/v1/documents/upload", files=files)
            assert response.status_code == 500

    def test_get_user_documents(self, client_with_auth, mock_db):
        """Test getting user documents."""
        with patch('src.app.crud.crud_documents.crud_documents.get_multi') as mock_get_multi:
            mock_get_multi.return_value = [
                {
                    "id": 1,
                    "title": "Document 1",
                    "filename": "doc1.pdf",
                    "file_type": "pdf",
                    "file_size": 1024,
                    "content": "Content 1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None
                },
                {
                    "id": 2,
                    "title": "Document 2",
                    "filename": "doc2.docx",
                    "file_type": "docx",
                    "file_size": 2048,
                    "content": "Content 2",
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": None
                }
            ]
            
            response = client_with_auth.get("/api/v1/documents/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "Document 1"
            assert data[1]["title"] == "Document 2"

    def test_get_document_success(self, client_with_auth, mock_db):
        """Test getting a specific document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get:
            mock_get.return_value = {
                "id": 1,
                "title": "Test Document",
                "filename": "test.pdf",
                "file_type": "pdf",
                "file_size": 1024,
                "content": "Test content",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None
            }
            
            response = client_with_auth.get("/api/v1/documents/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["title"] == "Test Document"

    def test_get_document_not_found(self, client_with_auth, mock_db):
        """Test getting a non-existent document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get:
            mock_get.return_value = None
            
            response = client_with_auth.get("/api/v1/documents/999")
            
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]

    def test_update_document_success(self, client_with_auth, mock_db):
        """Test updating a document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get, \
             patch('src.app.crud.crud_documents.crud_documents.update') as mock_update:
            
            mock_get.return_value = {"id": 1, "title": "Old Title"}
            mock_update.return_value = {
                "id": 1,
                "title": "New Title",
                "filename": "test.pdf",
                "file_type": "pdf",
                "file_size": 1024,
                "content": "Test content",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T01:00:00Z"
            }
            
            response = client_with_auth.put("/api/v1/documents/1?title=New Title")
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "New Title"

    def test_delete_document_success(self, client_with_auth, mock_db):
        """Test deleting a document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get, \
             patch('src.app.crud.crud_documents.crud_documents.db_delete') as mock_delete, \
             patch('src.app.services.file_upload.FileUploadService.delete_file') as mock_delete_file:
            
            mock_get.return_value = {"id": 1, "file_path": "/path/to/file.pdf"}
            mock_delete.return_value = None
            mock_delete_file.return_value = None
            
            response = client_with_auth.delete("/api/v1/documents/1")
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]

    def test_delete_document_not_found(self, client_with_auth, mock_db):
        """Test deleting a non-existent document."""
        with patch('src.app.crud.crud_documents.crud_documents.get') as mock_get:
            mock_get.return_value = None
            
            response = client_with_auth.delete("/api/v1/documents/999")
            
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]