from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import time
 
from app.domain.shared.exceptions import (
    AdapterError,
    AdapterTimeoutError,
    AdapterRateLimitError,
    AdapterAuthError,
    AdapterConfigError
)
from app import get_logger
 
logger = get_logger(__name__)


# ============================================================================
# Base Classes
# ============================================================================
 
@dataclass
class AdapterRequest:
    """Normalized request to any adapter."""
    task_id: str
    problem_statement: str
    public_tests: Optional[list] = None
    temperature: float = 0.7
    max_tokens: int = 2048
 
 
@dataclass
class AdapterResponse:
    """Normalized response from any adapter."""
    task_id: str
    response: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: str  # success, error, rate_limited, timeout
    error_message: Optional[str] = None
 
 
class CandidateAdapter(ABC):
    """
    Abstract base for all model adapters.
    Defines interface that all providers must implement.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.model_id = config.get("model_id", "unknown")
        self.provider = config.get("provider", "unknown")
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if model is reachable and authorized."""
        pass
    
    @abstractmethod
    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """Call the model and return normalized response."""
        pass
    
    @abstractmethod
    def estimate_cost(self, request: AdapterRequest) -> float:
        """Estimate cost without executing."""
        pass
    
    def get_capabilities(self) -> dict:
        """Return model metadata."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "max_tokens": self.config.get("max_tokens", 2048),
            "version": self.config.get("version", "unknown")
        }