"""Tests for document processing service."""

import io
import pytest
from unittest.mock import AsyncMock, patch

from src.app.services.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test cases for DocumentProcessor service."""

    @pytest.mark.asyncio
    async def test_validate_file_type_valid(self):
        """Test file type validation with valid extensions."""
        assert DocumentProcessor.validate_file_type("document.pdf") == "pdf"
        assert DocumentProcessor.validate_file_type("presentation.pptx") == "pptx"
        assert DocumentProcessor.validate_file_type("document.docx") == "docx"
        assert DocumentProcessor.validate_file_type("FILE.PDF") == "pdf"  # Case insensitive

    def test_validate_file_type_invalid(self):
        """Test file type validation with invalid extensions."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            DocumentProcessor.validate_file_type("document.txt")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            DocumentProcessor.validate_file_type("image.jpg")

    @pytest.mark.asyncio
    @patch('src.app.services.document_processor.PdfReader')
    async def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        # Mock PDF reader
        mock_page = AsyncMock()
        mock_page.extract_text.return_value = "Sample PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = b"fake pdf content"
        result = await DocumentProcessor.extract_text_from_pdf(content)
        
        assert result == "Sample PDF content"
        mock_pdf_reader.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.app.services.document_processor.PdfReader')
    async def test_extract_text_from_pdf_failure(self, mock_pdf_reader):
        """Test PDF text extraction failure."""
        mock_pdf_reader.side_effect = Exception("PDF parsing error")
        
        content = b"fake pdf content"
        with pytest.raises(Exception, match="Failed to extract text from PDF"):
            await DocumentProcessor.extract_text_from_pdf(content)

    @pytest.mark.asyncio
    @patch('src.app.services.document_processor.Presentation')
    async def test_extract_text_from_pptx_success(self, mock_presentation):
        """Test successful PPTX text extraction."""
        # Mock presentation
        mock_shape = AsyncMock()
        mock_shape.text = "Sample slide content"
        mock_slide = AsyncMock()
        mock_slide.shapes = [mock_shape]
        mock_presentation.return_value.slides = [mock_slide]
        
        content = b"fake pptx content"
        result = await DocumentProcessor.extract_text_from_pptx(content)
        
        assert "Slide 1:" in result
        assert "Sample slide content" in result

    @pytest.mark.asyncio
    @patch('src.app.services.document_processor.DocxDocument')
    async def test_extract_text_from_docx_success(self, mock_document):
        """Test successful DOCX text extraction."""
        # Mock document
        mock_paragraph = AsyncMock()
        mock_paragraph.text = "Sample document content"
        mock_document.return_value.paragraphs = [mock_paragraph]
        
        content = b"fake docx content"
        result = await DocumentProcessor.extract_text_from_docx(content)
        
        assert result == "Sample document content"

    @pytest.mark.asyncio
    async def test_process_document_pdf(self):
        """Test document processing for PDF files."""
        with patch.object(DocumentProcessor, 'extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "PDF content"
            
            result = await DocumentProcessor.process_document(b"content", "pdf")
            assert result == "PDF content"
            mock_extract.assert_called_once_with(b"content")

    @pytest.mark.asyncio
    async def test_process_document_pptx(self):
        """Test document processing for PPTX files."""
        with patch.object(DocumentProcessor, 'extract_text_from_pptx') as mock_extract:
            mock_extract.return_value = "PPTX content"
            
            result = await DocumentProcessor.process_document(b"content", "pptx")
            assert result == "PPTX content"
            mock_extract.assert_called_once_with(b"content")

    @pytest.mark.asyncio
    async def test_process_document_docx(self):
        """Test document processing for DOCX files."""
        with patch.object(DocumentProcessor, 'extract_text_from_docx') as mock_extract:
            mock_extract.return_value = "DOCX content"
            
            result = await DocumentProcessor.process_document(b"content", "docx")
            assert result == "DOCX content"
            mock_extract.assert_called_once_with(b"content")

    @pytest.mark.asyncio
    async def test_process_document_unsupported(self):
        """Test document processing with unsupported file type."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            await DocumentProcessor.process_document(b"content", "txt")