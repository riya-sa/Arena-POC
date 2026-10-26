"""Handle and report job errors."""

from enum import Enum
from typing import Optional
from datetime import datetime


class ErrorType(str, Enum):
    """Types of errors that can occur."""
    ADAPTER_ERROR = "adapter_error"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


class ErrorHandler:
    """Handle errors during job execution."""
    
    @staticmethod
    def categorize_error(error: Exception) -> ErrorType:
        """Categorize error type."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return ErrorType.TIMEOUT
        elif "adapter" in error_str or "provider" in error_str:
            return ErrorType.ADAPTER_ERROR
        elif "invalid" in error_str:
            return ErrorType.INVALID_INPUT
        elif "memory" in error_str or "resource" in error_str:
            return ErrorType.RESOURCE_ERROR
        else:
            return ErrorType.UNKNOWN
    
    @staticmethod
    def is_retryable(error_type: ErrorType) -> bool:
        """Determine if error should trigger retry."""
        retryable_errors = {
            ErrorType.TIMEOUT,
            ErrorType.ADAPTER_ERROR,
            ErrorType.RESOURCE_ERROR
        }
        return error_type in retryable_errors
    
    @staticmethod
    def log_error(
        job_id: str,
        task_id: str,
        error: Exception,
        attempt: int,
        is_retryable: bool
    ) -> dict:
        """Log error details."""
        error_type = ErrorHandler.categorize_error(error)
        
        return {
            "job_id": job_id,
            "task_id": task_id,
            "error_type": error_type.value,
            "error_message": str(error),
            "attempt": attempt,
            "is_retryable": is_retryable,
            "timestamp": datetime.utcnow().isoformat()
        }