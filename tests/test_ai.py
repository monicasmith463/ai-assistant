"""Comprehensive tests for AI functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.app.api.dependencies import get_ai_service, get_current_user
from src.app.core.ai.ai_service import AIService
from src.app.core.ai.llm_client import OpenAIClient
from tests.conftest import fake, override_dependency

from .helpers import generators, mocks


class MockOpenAIResponse:
    """Mock OpenAI API response."""
    
    def __init__(self, content: str = "Mock AI response"):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content


class MockAIService:
    """Mock AI service for testing."""
    
    def __init__(self):
        self.client = MagicMock()
        self.client.model = "gpt-3.5-turbo"
        self.client.max_tokens = 1000
        self.client.temperature = 0.7
        self.client.timeout = 30
    
    async def generate_code(self, description: str, language: str = None, 
                          framework: str = None, additional_requirements: str = None):
        """Mock code generation."""
        return {
            "generated_code": f"# Generated code for: {description}\nprint('Hello, World!')",
            "language": language,
            "framework": framework,
            "description": description,
            "metadata": {
                "input_tokens": 50,
                "output_tokens": 30,
                "total_tokens": 80,
                "model": "gpt-3.5-turbo"
            }
        }
    
    async def explain_code(self, code: str, focus_areas: str = None, 
                          target_audience: str = None):
        """Mock code explanation."""
        return {
            "explanation": f"This code does the following: {code[:50]}...",
            "original_code": code,
            "focus_areas": focus_areas,
            "target_audience": target_audience,
            "metadata": {
                "input_tokens": 60,
                "output_tokens": 40,
                "total_tokens": 100,
                "model": "gpt-3.5-turbo"
            }
        }
    
    async def review_code(self, code: str, review_type: str = None, 
                         specific_concerns: str = None):
        """Mock code review."""
        return {
            "review": f"Code review for: {code[:50]}... - Looks good overall!",
            "original_code": code,
            "review_type": review_type,
            "specific_concerns": specific_concerns,
            "metadata": {
                "input_tokens": 70,
                "output_tokens": 50,
                "total_tokens": 120,
                "model": "gpt-3.5-turbo"
            }
        }
    
    async def health_check(self):
        """Mock health check."""
        return {
            "status": "healthy",
            "service": "OpenAI",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "timeout": 30
        }
    
    def get_context_info(self):
        """Mock context info."""
        return {
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "timeout": 30,
            "available_operations": ["generate_code", "explain_code", "review_code"]
        }


@pytest.fixture
def mock_ai_service():
    """Fixture providing a mock AI service."""
    return MockAIService()


@pytest.fixture
def mock_redis_client():
    """Fixture providing a mock Redis client."""
    mock_client = AsyncMock()
    mock_client.get.return_value = None  # No cached data by default
    mock_client.setex.return_value = True
    return mock_client


class TestAIServiceInitialization:
    """Test AI service initialization and health checks."""
    
    def test_ai_service_initialization(self):
        """Test AI service can be initialized."""
        with patch('src.app.core.ai.ai_service.OpenAIClient') as mock_client:
            mock_client.return_value = MagicMock()
            service = AIService()
            assert service is not None
            assert service.client is not None
    
    def test_ai_service_with_custom_client(self):
        """Test AI service initialization with custom client."""
        mock_client = MagicMock()
        service = AIService(openai_client=mock_client)
        assert service.client == mock_client
    
    @patch('src.app.core.ai.llm_client.OPENAI_AVAILABLE', False)
    def test_ai_service_without_openai(self):
        """Test AI service behavior when OpenAI is not available."""
        service = AIService()
        assert service.client.client is None


class TestAIHealthCheck:
    """Test AI health check endpoint."""
    
    def test_ai_health_check_success(self, db: Session, client: TestClient, mock_ai_service):
        """Test successful AI health check."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        with patch('src.app.core.utils.cache.client', None):  # Disable caching
            response = client.get("/api/v1/ai/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "OpenAI"
        assert data["model"] == "gpt-3.5-turbo"
    
    def test_ai_health_check_with_caching(self, db: Session, client: TestClient, 
                                         mock_ai_service, mock_redis_client):
        """Test AI health check with caching."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        cached_response = {
            "status": "healthy",
            "service": "OpenAI",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "timeout": 30
        }
        mock_redis_client.get.return_value = json.dumps(cached_response)
        
        with patch('src.app.core.utils.cache.client', mock_redis_client):
            response = client.get("/api/v1/ai/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        mock_redis_client.get.assert_called_once()
    
    def test_ai_health_check_failure(self, db: Session, client: TestClient):
        """Test AI health check when service is unhealthy."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        
        # Mock a failing AI service
        failing_service = MockAIService()
        failing_service.health_check = AsyncMock(side_effect=Exception("Service unavailable"))
        override_dependency(get_ai_service, lambda: failing_service)
        
        with patch('src.app.core.utils.cache.client', None):
            response = client.get("/api/v1/ai/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data


class TestCodeGeneration:
    """Test code generation endpoint."""
    
    def test_generate_code_success(self, db: Session, client: TestClient, mock_ai_service):
        """Test successful code generation."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "description": "Create a function that calculates factorial",
            "language": "Python",
            "framework": None,
            "additional_requirements": "Include error handling"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "generated_code" in data
        assert data["language"] == "Python"
        assert data["description"] == request_data["description"]
        assert "metadata" in data
        assert data["metadata"]["model"] == "gpt-3.5-turbo"
    
    def test_generate_code_minimal_request(self, db: Session, client: TestClient, mock_ai_service):
        """Test code generation with minimal request data."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "description": "Create a simple hello world function"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "generated_code" in data
        assert data["description"] == request_data["description"]
    
    def test_generate_code_invalid_request(self, db: Session, client: TestClient, mock_ai_service):
        """Test code generation with invalid request data."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        # Description too short
        request_data = {
            "description": "short"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_generate_code_ai_service_error(self, db: Session, client: TestClient):
        """Test code generation when AI service fails."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        
        # Mock failing AI service
        failing_service = MockAIService()
        failing_service.generate_code = AsyncMock(side_effect=Exception("AI service error"))
        override_dependency(get_ai_service, lambda: failing_service)
        
        request_data = {
            "description": "Create a function that calculates factorial"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to generate code" in response.json()["detail"]
    
    def test_generate_code_rate_limit_error(self, db: Session, client: TestClient):
        """Test code generation when rate limit is exceeded."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        
        # Mock AI service with rate limit error
        failing_service = MockAIService()
        failing_service.generate_code = AsyncMock(side_effect=Exception("rate limit exceeded"))
        override_dependency(get_ai_service, lambda: failing_service)
        
        request_data = {
            "description": "Create a function that calculates factorial"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "rate limit exceeded" in response.json()["detail"].lower()
    
    def test_generate_code_timeout_error(self, db: Session, client: TestClient):
        """Test code generation when request times out."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        
        # Mock AI service with timeout error
        failing_service = MockAIService()
        failing_service.generate_code = AsyncMock(side_effect=Exception("timeout occurred"))
        override_dependency(get_ai_service, lambda: failing_service)
        
        request_data = {
            "description": "Create a function that calculates factorial"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert "timed out" in response.json()["detail"].lower()


class TestCodeExplanation:
    """Test code explanation endpoint."""
    
    def test_explain_code_success(self, db: Session, client: TestClient, mock_ai_service):
        """Test successful code explanation."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
            "focus_areas": "recursion",
            "target_audience": "beginner"
        }
        
        with patch('src.app.core.utils.cache.client', None):  # Disable caching
            response = client.post("/api/v1/ai/explain-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "explanation" in data
        assert data["original_code"] == request_data["code"]
        assert data["focus_areas"] == request_data["focus_areas"]
        assert data["target_audience"] == request_data["target_audience"]
        assert "metadata" in data
    
    def test_explain_code_with_caching(self, db: Session, client: TestClient, 
                                      mock_ai_service, mock_redis_client):
        """Test code explanation with caching."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "code": "print('Hello, World!')",
            "focus_areas": None,
            "target_audience": None
        }
        
        cached_response = {
            "explanation": "This code prints Hello World",
            "original_code": request_data["code"],
            "focus_areas": None,
            "target_audience": None,
            "metadata": {
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "model": "gpt-3.5-turbo"
            }
        }
        mock_redis_client.get.return_value = json.dumps(cached_response)
        
        with patch('src.app.core.utils.cache.client', mock_redis_client):
            response = client.post("/api/v1/ai/explain-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["explanation"] == cached_response["explanation"]
        mock_redis_client.get.assert_called_once()
    
    def test_explain_code_minimal_request(self, db: Session, client: TestClient, mock_ai_service):
        """Test code explanation with minimal request data."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "code": "print('Hello, World!')"
        }
        
        with patch('src.app.core.utils.cache.client', None):
            response = client.post("/api/v1/ai/explain-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "explanation" in data
        assert data["original_code"] == request_data["code"]
    
    def test_explain_code_invalid_request(self, db: Session, client: TestClient, mock_ai_service):
        """Test code explanation with invalid request data."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        # Code too short
        request_data = {
            "code": "x"
        }
        
        response = client.post("/api/v1/ai/explain-code", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCodeReview:
    """Test code review endpoint."""
    
    def test_review_code_success(self, db: Session, client: TestClient, mock_ai_service):
        """Test successful code review."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "code": "def process_data(data):\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result",
            "review_type": "performance",
            "specific_concerns": "efficiency of the loop"
        }
        
        with patch('src.app.core.utils.cache.client', None):  # Disable caching
            response = client.post("/api/v1/ai/review-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "review" in data
        assert data["original_code"] == request_data["code"]
        assert data["review_type"] == request_data["review_type"]
        assert data["specific_concerns"] == request_data["specific_concerns"]
        assert "metadata" in data
    
    def test_review_code_with_caching(self, db: Session, client: TestClient, 
                                     mock_ai_service, mock_redis_client):
        """Test code review with caching."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        request_data = {
            "code": "print('test')",
            "review_type": "general",
            "specific_concerns": None
        }
        
        cached_response = {
            "review": "Code looks good",
            "original_code": request_data["code"],
            "review_type": "general",
            "specific_concerns": None,
            "metadata": {
                "input_tokens": 15,
                "output_tokens": 25,
                "total_tokens": 40,
                "model": "gpt-3.5-turbo"
            }
        }
        mock_redis_client.get.return_value = json.dumps(cached_response)
        
        with patch('src.app.core.utils.cache.client', mock_redis_client):
            response = client.post("/api/v1/ai/review-code", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["review"] == cached_response["review"]
        mock_redis_client.get.assert_called_once()


class TestAIContext:
    """Test AI context endpoint."""
    
    def test_get_ai_context_success(self, db: Session, client: TestClient, mock_ai_service):
        """Test successful AI context retrieval."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        with patch('src.app.core.utils.cache.client', None):  # Disable caching
            response = client.get("/api/v1/ai/context")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model"] == "gpt-3.5-turbo"
        assert data["max_tokens"] == 1000
        assert data["temperature"] == 0.7
        assert data["timeout"] == 30
        assert "available_operations" in data
        assert len(data["available_operations"]) == 3


class TestRateLimiting:
    """Test rate limiting functionality for AI endpoints."""
    
    @patch('src.app.api.dependencies.is_rate_limited')
    def test_rate_limiting_applied(self, mock_rate_limited, db: Session, 
                                  client: TestClient, mock_ai_service):
        """Test that rate limiting is applied to AI endpoints."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        # Mock rate limiting to return True (rate limited)
        mock_rate_limited.return_value = True
        
        request_data = {
            "description": "Create a simple function"
        }
        
        with patch('src.app.api.dependencies.crud_tiers.get', return_value=None):
            response = client.post("/api/v1/ai/generate-code", json=request_data)
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Rate limit exceeded" in response.json()["detail"]


class TestAuthentication:
    """Test authentication requirements for AI endpoints."""
    
    def test_ai_endpoints_require_authentication(self, client: TestClient):
        """Test that AI endpoints require authentication."""
        endpoints = [
            ("/api/v1/ai/generate-code", "POST", {"description": "test"}),
            ("/api/v1/ai/explain-code", "POST", {"code": "print('test')"}),
            ("/api/v1/ai/review-code", "POST", {"code": "print('test')"}),
            ("/api/v1/ai/health", "GET", None),
            ("/api/v1/ai/context", "GET", None),
        ]
        
        for endpoint, method, data in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOpenAIClient:
    """Test OpenAI client functionality."""
    
    @patch('src.app.core.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('src.app.core.ai.llm_client.AsyncOpenAI')
    def test_openai_client_initialization(self, mock_openai):
        """Test OpenAI client initialization."""
        mock_openai.return_value = MagicMock()
        
        client = OpenAIClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "gpt-3.5-turbo"  # Default from settings
        mock_openai.assert_called_once_with(api_key="test-key")
    
    @patch('src.app.core.ai.llm_client.OPENAI_AVAILABLE', False)
    def test_openai_client_without_library(self):
        """Test OpenAI client when library is not available."""
        client = OpenAIClient()
        assert client.client is None
    
    def test_token_counting_without_tiktoken(self):
        """Test token counting when tiktoken is not available."""
        with patch('src.app.core.ai.llm_client.TIKTOKEN_AVAILABLE', False):
            client = OpenAIClient()
            tokens = client.count_tokens("Hello world")
            # Should use approximation: len(text) // 4
            assert tokens == len("Hello world") // 4
    
    @patch('src.app.core.ai.llm_client.TIKTOKEN_AVAILABLE', True)
    @patch('src.app.core.ai.llm_client.tiktoken')
    def test_token_counting_with_tiktoken(self, mock_tiktoken):
        """Test token counting when tiktoken is available."""
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoder
        
        client = OpenAIClient()
        tokens = client.count_tokens("Hello world")
        assert tokens == 5
        mock_encoder.encode.assert_called_once_with("Hello world")
    
    @patch('src.app.core.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('src.app.core.ai.llm_client.AsyncOpenAI')
    async def test_health_check_success(self, mock_openai):
        """Test successful health check."""
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key="test-key")
        is_healthy = await client.health_check()
        assert is_healthy is True
    
    @patch('src.app.core.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('src.app.core.ai.llm_client.AsyncOpenAI')
    async def test_health_check_failure(self, mock_openai):
        """Test health check failure."""
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        client = OpenAIClient(api_key="test-key")
        is_healthy = await client.health_check()
        assert is_healthy is False


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""
    
    def test_ai_service_dependency_failure(self, db: Session, client: TestClient):
        """Test behavior when AI service dependency fails to initialize."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        
        # Mock get_ai_service to raise an exception
        def failing_ai_service():
            raise Exception("AI service initialization failed")
        
        override_dependency(get_ai_service, failing_ai_service)
        
        request_data = {
            "description": "Create a simple function"
        }
        
        response = client.post("/api/v1/ai/generate-code", json=request_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_cache_failure_graceful_degradation(self, db: Session, client: TestClient, 
                                               mock_ai_service):
        """Test graceful degradation when cache fails."""
        user = generators.create_user(db)
        override_dependency(get_current_user, mocks.get_current_user(user))
        override_dependency(get_ai_service, lambda: mock_ai_service)
        
        # Mock Redis client that fails
        failing_redis = AsyncMock()
        failing_redis.get.side_effect = Exception("Redis connection failed")
        failing_redis.setex.side_effect = Exception("Redis connection failed")
        
        request_data = {
            "code": "print('Hello, World!')"
        }
        
        with patch('src.app.core.utils.cache.client', failing_redis):
            response = client.post("/api/v1/ai/explain-code", json=request_data)
        
        # Should still work despite cache failure
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "explanation" in data