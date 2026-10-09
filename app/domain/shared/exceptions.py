"""
Shared exceptions for all domains.
Single source of truth for error handling.
"""

from typing import Any, Dict, Optional


class ArenaException(Exception):
    """Base exception for all arena errors."""

    http_status: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None, **kwargs
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        for key, value in kwargs.items():
            setattr(self, key, value)


# ============================================================================
# Benchmark Domain Exceptions
# ============================================================================


class BenchmarkNotFoundError(ArenaException):
    """Benchmark suite or version not found."""

    http_status = 404
    error_code = "BENCHMARK_NOT_FOUND"


class BenchmarkAlreadyPublishedError(ArenaException):
    """Cannot modify published benchmark."""

    http_status = 400
    error_code = "BENCHMARK_ALREADY_PUBLISHED"


class BenchmarkVersionNotFoundError(ArenaException):
    """Benchmark version not found."""

    http_status = 404
    error_code = "BENCHMARK_VERSION_NOT_FOUND"


class TaskNotFoundError(ArenaException):
    """Task not found in benchmark."""

    http_status = 404
    error_code = "TASK_NOT_FOUND"


class InvalidTaskError(ArenaException):
    """Task validation failed."""

    http_status = 400
    error_code = "INVALID_TASK"


# ============================================================================
# Candidate Domain Exceptions
# ============================================================================


class CandidateNotFoundError(ArenaException):
    """Model candidate not found."""

    http_status = 404
    error_code = "CANDIDATE_NOT_FOUND"


class CandidateVersionNotFoundError(ArenaException):
    """Candidate version not found."""

    http_status = 404
    error_code = "CANDIDATE_VERSION_NOT_FOUND"


class InvalidCandidateError(ArenaException):
    """Candidate validation failed."""

    http_status = 400
    error_code = "INVALID_CANDIDATE"


# ============================================================================
# Experiment Domain Exceptions
# ============================================================================


class ExperimentNotFoundError(ArenaException):
    """Experiment not found."""

    http_status = 404
    error_code = "EXPERIMENT_NOT_FOUND"


class ExperimentInvalidStateError(ArenaException):
    """Cannot perform action in current experiment state."""

    http_status = 400
    error_code = "EXPERIMENT_INVALID_STATE"


class ExecutionNotFoundError(ArenaException):
    """Execution not found."""

    http_status = 404
    error_code = "EXECUTION_NOT_FOUND"


class InsufficientBudgetError(ArenaException):
    """Experiment cost exceeds budget."""

    http_status = 402
    error_code = "INSUFFICIENT_BUDGET"


class ExperimentCancelledError(ArenaException):
    """Cannot operate on cancelled experiment."""

    http_status = 400
    error_code = "EXPERIMENT_CANCELLED"


# ============================================================================
# Adapter Domain Exceptions
# ============================================================================


class AdapterError(ArenaException):
    """Generic adapter error."""

    http_status = 503
    error_code = "ADAPTER_ERROR"


class AdapterNotFoundError(AdapterError):
    """Adapter type not found."""

    http_status = 400
    error_code = "ADAPTER_NOT_FOUND"


class AdapterHealthCheckError(AdapterError):
    """Adapter health check failed."""

    http_status = 503
    error_code = "ADAPTER_UNHEALTHY"


class AdapterTimeoutError(AdapterError):
    """Adapter request timed out."""

    http_status = 504
    error_code = "ADAPTER_TIMEOUT"


class AdapterRateLimitError(AdapterError):
    """Adapter rate limit exceeded."""

    http_status = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class AdapterAuthError(AdapterError):
    """Adapter authentication failed."""

    http_status = 401
    error_code = "ADAPTER_AUTH_FAILED"


class AdapterConfigError(AdapterError):
    """Adapter configuration invalid."""

    http_status = 400
    error_code = "ADAPTER_CONFIG_INVALID"


# ============================================================================
# Validation & Data Exceptions
# ============================================================================


class ValidationError(ArenaException):
    """Input validation failed."""

    http_status = 400
    error_code = "VALIDATION_ERROR"


class DataNotFoundError(ArenaException):
    """Required data not found."""

    http_status = 404
    error_code = "DATA_NOT_FOUND"


class DataAlreadyExistsError(ArenaException):
    """Data with same key already exists."""

    http_status = 409
    error_code = "DATA_ALREADY_EXISTS"


# ============================================================================
# Security Exceptions
# ============================================================================


class UnauthorizedError(ArenaException):
    """User not authorized."""

    http_status = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(ArenaException):
    """User lacks permission."""

    http_status = 403
    error_code = "FORBIDDEN"


class SecurityPolicyViolationError(ArenaException):
    """Security policy violated."""

    http_status = 403
    error_code = "SECURITY_POLICY_VIOLATION"


# ============================================================================
# System Exceptions
# ============================================================================


class DatabaseError(ArenaException):
    """Database operation failed."""

    http_status = 500
    error_code = "DATABASE_ERROR"


class QueueError(ArenaException):
    """Job queue operation failed."""

    http_status = 500
    error_code = "QUEUE_ERROR"


class ServiceUnavailableError(ArenaException):
    """Required service unavailable."""

    http_status = 503
    error_code = "SERVICE_UNAVAILABLE"
