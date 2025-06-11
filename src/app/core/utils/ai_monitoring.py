"""AI operation monitoring and metrics utilities."""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from ..logger import logging

logger = logging.getLogger(__name__)


class AIMetrics:
    """Class to track AI operation metrics."""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_cost_estimate = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.average_response_time = 0.0
        self._response_times = []
    
    def record_request(self, success: bool, tokens: int = 0, response_time: float = 0.0, 
                      cost_estimate: float = 0.0, cache_hit: bool = False):
        """Record metrics for an AI request.
        
        Args:
            success: Whether the request was successful
            tokens: Number of tokens used
            response_time: Response time in seconds
            cost_estimate: Estimated cost in USD
            cache_hit: Whether this was a cache hit
        """
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.total_tokens_used += tokens
        self.total_cost_estimate += cost_estimate
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if response_time > 0:
            self._response_times.append(response_time)
            self.average_response_time = sum(self._response_times) / len(self._response_times)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics.
        
        Returns:
            Dictionary containing current metrics
        """
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate_percent": round(success_rate, 2),
            "total_tokens_used": self.total_tokens_used,
            "total_cost_estimate_usd": round(self.total_cost_estimate, 4),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "average_response_time_seconds": round(self.average_response_time, 3)
        }
    
    def reset(self):
        """Reset all metrics to zero."""
        self.__init__()


# Global metrics instance
ai_metrics = AIMetrics()


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate the cost of an AI operation based on token usage.
    
    Args:
        model: The AI model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    # Pricing as of 2024 (prices may change)
    pricing = {
        "gpt-3.5-turbo": {
            "input": 0.0015 / 1000,   # $0.0015 per 1K input tokens
            "output": 0.002 / 1000    # $0.002 per 1K output tokens
        },
        "gpt-4": {
            "input": 0.03 / 1000,     # $0.03 per 1K input tokens
            "output": 0.06 / 1000     # $0.06 per 1K output tokens
        },
        "gpt-4-turbo-preview": {
            "input": 0.01 / 1000,     # $0.01 per 1K input tokens
            "output": 0.03 / 1000     # $0.03 per 1K output tokens
        }
    }
    
    model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])  # Default to gpt-3.5-turbo
    
    input_cost = input_tokens * model_pricing["input"]
    output_cost = output_tokens * model_pricing["output"]
    
    return input_cost + output_cost


@asynccontextmanager
async def monitor_ai_operation(operation_type: str, user_id: Optional[int] = None, 
                              model: str = "gpt-3.5-turbo"):
    """Context manager to monitor AI operations.
    
    Args:
        operation_type: Type of operation (generate_code, explain_code, etc.)
        user_id: ID of the user making the request
        model: AI model being used
        
    Yields:
        Dictionary to store operation results
    """
    start_time = time.time()
    operation_data = {
        "success": False,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cache_hit": False,
        "error": None
    }
    
    logger.info(f"Starting AI operation: {operation_type} for user {user_id}")
    
    try:
        yield operation_data
        operation_data["success"] = True
        
    except Exception as e:
        operation_data["error"] = str(e)
        logger.error(f"AI operation {operation_type} failed for user {user_id}: {e}")
        raise
        
    finally:
        end_time = time.time()
        response_time = end_time - start_time
        
        # Calculate cost estimate
        cost_estimate = estimate_cost(
            model, 
            operation_data["input_tokens"], 
            operation_data["output_tokens"]
        )
        
        # Record metrics
        ai_metrics.record_request(
            success=operation_data["success"],
            tokens=operation_data["total_tokens"],
            response_time=response_time,
            cost_estimate=cost_estimate,
            cache_hit=operation_data["cache_hit"]
        )
        
        # Log operation completion
        if operation_data["success"]:
            logger.info(
                f"AI operation {operation_type} completed for user {user_id}: "
                f"tokens={operation_data['total_tokens']}, "
                f"time={response_time:.2f}s, "
                f"cost=${cost_estimate:.4f}, "
                f"cache_hit={operation_data['cache_hit']}"
            )
        else:
            logger.error(
                f"AI operation {operation_type} failed for user {user_id}: "
                f"error={operation_data['error']}, "
                f"time={response_time:.2f}s"
            )


def log_token_usage(operation: str, user_id: Optional[int], input_tokens: int, 
                   output_tokens: int, model: str):
    """Log detailed token usage information.
    
    Args:
        operation: Type of AI operation
        user_id: User ID
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: AI model used
    """
    total_tokens = input_tokens + output_tokens
    cost_estimate = estimate_cost(model, input_tokens, output_tokens)
    
    logger.info(
        f"Token usage - Operation: {operation}, User: {user_id}, "
        f"Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}, "
        f"Model: {model}, Cost: ${cost_estimate:.4f}"
    )


def log_cache_operation(operation: str, cache_key: str, hit: bool, user_id: Optional[int] = None):
    """Log cache hit/miss information.
    
    Args:
        operation: Type of operation
        cache_key: Cache key used
        hit: Whether it was a cache hit
        user_id: User ID (optional)
    """
    status = "HIT" if hit else "MISS"
    logger.info(f"Cache {status} - Operation: {operation}, Key: {cache_key[:20]}..., User: {user_id}")


def log_rate_limit_info(user_id: Optional[int], endpoint: str, remaining_requests: int, 
                       reset_time: Optional[int] = None):
    """Log rate limiting information.
    
    Args:
        user_id: User ID
        endpoint: API endpoint
        remaining_requests: Number of remaining requests
        reset_time: When the rate limit resets (timestamp)
    """
    logger.info(
        f"Rate limit info - User: {user_id}, Endpoint: {endpoint}, "
        f"Remaining: {remaining_requests}, Reset: {reset_time}"
    )


def get_ai_metrics() -> Dict[str, Any]:
    """Get current AI metrics.
    
    Returns:
        Dictionary containing current AI metrics
    """
    return ai_metrics.get_stats()


def reset_ai_metrics():
    """Reset AI metrics to zero."""
    ai_metrics.reset()
    logger.info("AI metrics have been reset")