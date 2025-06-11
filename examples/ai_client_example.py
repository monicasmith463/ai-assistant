#!/usr/bin/env python3
"""
AI Code Assistant Client Example

This script demonstrates how to use the AI Code Assistant API endpoints.
It shows proper authentication, error handling, and usage of all three main endpoints:
- Code Generation
- Code Explanation  
- Code Review

Prerequisites:
1. FastAPI server running (default: http://localhost:8000)
2. Valid user account with authentication token
3. OpenAI API key configured in the server

Usage:
    python examples/ai_client_example.py

Environment Variables:
    API_BASE_URL: Base URL for the API (default: http://localhost:8000)
    JWT_TOKEN: Authentication token (required)
    
Example:
    export JWT_TOKEN="your-jwt-token-here"
    python examples/ai_client_example.py
"""

import asyncio
import json
import os
import sys
from typing import Dict, Optional

import aiohttp


class AIAssistantClient:
    """Client for interacting with the AI Code Assistant API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        """Initialize the AI Assistant client.
        
        Args:
            base_url: Base URL for the API
            token: JWT authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request data for POST requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails or returns error status
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")
            
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    error_detail = response_data.get("detail", "Unknown error")
                    raise Exception(f"API Error ({response.status}): {error_detail}")
                
                return response_data
                
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except asyncio.TimeoutError:
            raise Exception("Request timed out")
    
    async def generate_code(
        self,
        description: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        additional_requirements: Optional[str] = None
    ) -> Dict:
        """Generate code from natural language description.
        
        Args:
            description: Description of what code to generate
            language: Programming language (optional)
            framework: Framework to use (optional)
            additional_requirements: Additional requirements (optional)
            
        Returns:
            Generated code response
        """
        data = {"description": description}
        if language:
            data["language"] = language
        if framework:
            data["framework"] = framework
        if additional_requirements:
            data["additional_requirements"] = additional_requirements
            
        return await self._make_request("POST", "/api/v1/ai/generate-code", data)
    
    async def explain_code(
        self,
        code: str,
        focus_areas: Optional[str] = None,
        target_audience: Optional[str] = None
    ) -> Dict:
        """Explain existing code.
        
        Args:
            code: Code to explain
            focus_areas: Specific areas to focus on (optional)
            target_audience: Target audience level (optional)
            
        Returns:
            Code explanation response
        """
        data = {"code": code}
        if focus_areas:
            data["focus_areas"] = focus_areas
        if target_audience:
            data["target_audience"] = target_audience
            
        return await self._make_request("POST", "/api/v1/ai/explain-code", data)
    
    async def review_code(
        self,
        code: str,
        review_type: Optional[str] = None,
        specific_concerns: Optional[str] = None
    ) -> Dict:
        """Review code and provide suggestions.
        
        Args:
            code: Code to review
            review_type: Type of review (security, performance, etc.)
            specific_concerns: Specific concerns to address (optional)
            
        Returns:
            Code review response
        """
        data = {"code": code}
        if review_type:
            data["review_type"] = review_type
        if specific_concerns:
            data["specific_concerns"] = specific_concerns
            
        return await self._make_request("POST", "/api/v1/ai/review-code", data)
    
    async def health_check(self) -> Dict:
        """Check AI service health status.
        
        Returns:
            Health status response
        """
        return await self._make_request("GET", "/api/v1/ai/health")
    
    async def get_context(self) -> Dict:
        """Get AI service context information.
        
        Returns:
            Context information response
        """
        return await self._make_request("GET", "/api/v1/ai/context")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_response(response: Dict, title: str = "Response"):
    """Print a formatted API response."""
    print(f"\n{title}:")
    print("-" * 40)
    
    # Pretty print the response
    if isinstance(response, dict):
        for key, value in response.items():
            if key == "metadata":
                print(f"{key}:")
                for meta_key, meta_value in value.items():
                    print(f"  {meta_key}: {meta_value}")
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings for readability
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")
    else:
        print(json.dumps(response, indent=2))


async def demonstrate_code_generation(client: AIAssistantClient):
    """Demonstrate code generation functionality."""
    print_section("CODE GENERATION EXAMPLES")
    
    examples = [
        {
            "title": "Simple Python Function",
            "description": "Create a Python function that calculates the factorial of a number",
            "language": "Python",
            "additional_requirements": "Include error handling for negative numbers and type hints"
        },
        {
            "title": "FastAPI Endpoint",
            "description": "Create a REST API endpoint for user registration",
            "language": "Python",
            "framework": "FastAPI",
            "additional_requirements": "Include input validation and proper HTTP status codes"
        },
        {
            "title": "JavaScript Function",
            "description": "Create a function to validate email addresses",
            "language": "JavaScript",
            "additional_requirements": "Use regex pattern and return boolean"
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['title']}")
        print(f"Description: {example['description']}")
        
        try:
            response = await client.generate_code(
                description=example["description"],
                language=example.get("language"),
                framework=example.get("framework"),
                additional_requirements=example.get("additional_requirements")
            )
            print_response(response, "Generated Code")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def demonstrate_code_explanation(client: AIAssistantClient):
    """Demonstrate code explanation functionality."""
    print_section("CODE EXPLANATION EXAMPLES")
    
    examples = [
        {
            "title": "Recursive Function",
            "code": """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)""",
            "focus_areas": "recursion and base case",
            "target_audience": "beginner"
        },
        {
            "title": "List Comprehension",
            "code": "squares = [x**2 for x in range(10) if x % 2 == 0]",
            "focus_areas": "list comprehension syntax",
            "target_audience": "intermediate"
        },
        {
            "title": "Async Function",
            "code": """async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()""",
            "focus_areas": "async/await pattern",
            "target_audience": "advanced"
        }
    ]
    
    for example in examples:
        print(f"\n📖 {example['title']}")
        print(f"Code to explain:\n{example['code']}")
        
        try:
            response = await client.explain_code(
                code=example["code"],
                focus_areas=example.get("focus_areas"),
                target_audience=example.get("target_audience")
            )
            print_response(response, "Explanation")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def demonstrate_code_review(client: AIAssistantClient):
    """Demonstrate code review functionality."""
    print_section("CODE REVIEW EXAMPLES")
    
    examples = [
        {
            "title": "Performance Review",
            "code": """def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result""",
            "review_type": "performance",
            "specific_concerns": "efficiency and memory usage"
        },
        {
            "title": "Security Review",
            "code": """def login(username, password):
    if username == "admin" and password == "password123":
        return "Access granted"
    return "Access denied" """,
            "review_type": "security",
            "specific_concerns": "authentication vulnerabilities"
        },
        {
            "title": "Best Practices Review",
            "code": """def calculate(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b""",
            "review_type": "best_practices",
            "specific_concerns": "error handling and code structure"
        }
    ]
    
    for example in examples:
        print(f"\n🔍 {example['title']}")
        print(f"Code to review:\n{example['code']}")
        
        try:
            response = await client.review_code(
                code=example["code"],
                review_type=example.get("review_type"),
                specific_concerns=example.get("specific_concerns")
            )
            print_response(response, "Review")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def demonstrate_service_info(client: AIAssistantClient):
    """Demonstrate service information endpoints."""
    print_section("SERVICE INFORMATION")
    
    print("\n🏥 Health Check")
    try:
        health = await client.health_check()
        print_response(health, "Health Status")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n📋 Context Information")
    try:
        context = await client.get_context()
        print_response(context, "Service Context")
    except Exception as e:
        print(f"❌ Context retrieval failed: {e}")


async def main():
    """Main demonstration function."""
    print("🤖 AI Code Assistant Client Example")
    print("=" * 60)
    
    # Get configuration from environment
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    token = os.getenv("JWT_TOKEN")
    
    if not token:
        print("❌ Error: JWT_TOKEN environment variable is required")
        print("\nTo get a token:")
        print("1. Register/login through the API: POST /api/v1/login")
        print("2. Set the token: export JWT_TOKEN='your-token-here'")
        print("3. Run this script again")
        sys.exit(1)
    
    print(f"🌐 API Base URL: {base_url}")
    print(f"🔑 Using authentication token: {token[:20]}...")
    
    try:
        async with AIAssistantClient(base_url=base_url, token=token) as client:
            # Demonstrate all functionality
            await demonstrate_service_info(client)
            await demonstrate_code_generation(client)
            await demonstrate_code_explanation(client)
            await demonstrate_code_review(client)
            
            print_section("DEMONSTRATION COMPLETE")
            print("✅ All AI Code Assistant features demonstrated successfully!")
            print("\nNext steps:")
            print("- Integrate these examples into your application")
            print("- Customize prompts for your specific use cases")
            print("- Monitor token usage and costs")
            print("- Implement proper error handling and retry logic")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure the FastAPI server is running")
        print("2. Verify your JWT token is valid and not expired")
        print("3. Check that OpenAI API key is configured on the server")
        print("4. Confirm Redis is running for caching functionality")
        sys.exit(1)


if __name__ == "__main__":
    # Check if required dependencies are available
    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp is required to run this example")
        print("Install it with: pip install aiohttp")
        sys.exit(1)
    
    # Run the demonstration
    asyncio.run(main())