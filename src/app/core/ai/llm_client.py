"""OpenAI client wrapper for the AI assistant."""

import asyncio
import logging
from typing import Any, Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None

try:
    from openai import AsyncOpenAI
    from openai.types.chat import ChatCompletion
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    ChatCompletion = None

from ..config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client wrapper with error handling and token counting utilities."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, uses settings.OPENAI_API_KEY
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available. Client will not be functional.")
            self.client = None
        else:
            self.api_key = api_key or settings.OPENAI_API_KEY
            if not self.api_key:
                logger.warning("OpenAI API key not provided. Client will not be functional.")
                self.client = None
            else:
                self.client = AsyncOpenAI(api_key=self.api_key)

        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.timeout = settings.AI_TIMEOUT

        # Initialize tokenizer for token counting
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Fallback to cl100k_base encoding for newer models
                try:
                    self.tokenizer = tiktoken.get_encoding("cl100k_base")
                except Exception:
                    logger.warning("Failed to initialize tiktoken. Token counting will use approximation.")
                    self.tokenizer = None
        else:
            logger.warning("tiktoken not available. Token counting will use approximation.")
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens in the text
        """
        if not self.tokenizer:
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4

        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4

    def count_messages_tokens(self, messages: list[dict[str, str]]) -> int:
        """Count tokens in a list of chat messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            Total number of tokens in all messages
        """
        total_tokens = 0
        for message in messages:
            # Add tokens for message content
            total_tokens += self.count_tokens(message.get("content", ""))
            # Add overhead tokens for message structure (role, etc.)
            total_tokens += 4  # Approximate overhead per message

        # Add overhead for the conversation structure
        total_tokens += 2

        return total_tokens

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Create a chat completion with error handling.

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters for the API call

        Returns:
            ChatCompletion response from OpenAI

        Raises:
            Exception: If the API call fails
        """
        if not self.client:
            raise Exception("OpenAI client not initialized. Please provide a valid API key.")

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model or self.model,
                    messages=messages,
                    max_tokens=max_tokens or self.max_tokens,
                    temperature=temperature if temperature is not None else self.temperature,
                    **kwargs,
                ),
                timeout=self.timeout,
            )
            return response
        except TimeoutError:
            logger.error(f"OpenAI API call timed out after {self.timeout} seconds")
            raise Exception(f"AI request timed out after {self.timeout} seconds")
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise Exception(f"AI service error: {str(e)}")

    async def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The user prompt
            system_message: Optional system message to set context
            **kwargs: Additional parameters for the API call

        Returns:
            Generated text response
        """
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.append({"role": "user", "content": prompt})

        # Check token count
        token_count = self.count_messages_tokens(messages)
        if token_count > (self.max_tokens * 0.8):  # Leave room for response
            logger.warning(f"Input token count ({token_count}) is high, may exceed limits")

        response = await self.chat_completion(messages, **kwargs)

        if not response.choices:
            raise Exception("No response generated from AI service")

        return response.choices[0].message.content or ""

    async def health_check(self) -> bool:
        """Check if the OpenAI service is accessible.

        Returns:
            True if the service is accessible, False otherwise
        """
        try:
            await self.generate_text("Hello", max_tokens=5)
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
