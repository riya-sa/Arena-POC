"""Retry logic for failed tasks."""

import asyncio
from typing import Callable, Any
from datetime import datetime, timedelta
from app.logger import logger


class RetryPolicy:
    """Define retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay_seconds: float = 1,
        max_delay_seconds: float = 60,
        backoff_multiplier: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.backoff_multiplier = backoff_multiplier
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)


class RetryManager:
    """Manage retries for failed operations."""
    
    def __init__(self, policy: RetryPolicy = None):
        self.policy = policy or RetryPolicy()
        self.retry_log = {}
    
    async def execute_with_retry(
        self,
        operation_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with automatic retries on failure."""
        attempt = 0
        last_error = None
        
        while attempt <= self.policy.max_retries:
            try:
                logger.debug(f"Executing {operation_id} (attempt {attempt + 1})")
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"{operation_id} succeeded on retry {attempt}")
                
                return result
            
            except Exception as e:
                last_error = e
                attempt += 1
                
                if attempt <= self.policy.max_retries:
                    delay = self.policy.get_delay(attempt - 1)
                    logger.warning(
                        f"{operation_id} failed (attempt {attempt}/{self.policy.max_retries + 1}), "
                        f"retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{operation_id} failed after {attempt} attempts: {str(e)}")
        
        raise last_error or RuntimeError("Operation failed after all retries")
    
    def record_retry(self, job_id: str, task_id: str, attempt: int, error: str):
        """Record retry attempt."""
        key = f"{job_id}:{task_id}"
        if key not in self.retry_log:
            self.retry_log[key] = []
        
        self.retry_log[key].append({
            "attempt": attempt,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        })


# Global retry manager
retry_manager = RetryManager()


def get_retry_manager() -> RetryManager:
    """Get global retry manager."""
    return retry_manager