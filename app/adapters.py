"""
Candidate adapter abstraction - standard interface for all models
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import time
import uuid

from app.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class AdapterRequest:
    """Request to model adapter."""
    task_id: str
    problem_statement: str
    public_tests: list = None
    
    # Configuration (immutable during experiment)
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class AdapterResponse:
    """Response from model adapter."""
    task_id: str
    response: str  # Full response (may include explanation + code)
    
    # Telemetry
    input_tokens: int
    output_tokens: int
    latency_ms: int
    
    # Status
    status: str  # "success", "error", "rate_limited", "timeout"
    error_message: Optional[str] = None


class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass


class AdapterTimeoutError(AdapterError):
    """Request timed out."""
    pass


class AdapterRateLimitError(AdapterError):
    """Rate limit hit."""
    pass


class AdapterAuthError(AdapterError):
    """Authentication failed."""
    pass


class AdapterAPIError(AdapterError):
    """API returned error."""
    pass


class CandidateAdapter(ABC):
    """
    Abstract base for all model adapters.
    Subclasses: OpenAIAdapter, AnthropicAdapter, LocalInferenceAdapter, MockAdapter
    """
    
    def __init__(self, config: dict):
        """
        Initialize adapter.
        
        Args:
            config: {
                "model_id": "claude-3-5-sonnet",
                "temperature": 0.7,
                "max_tokens": 2048,
                "api_endpoint": "...",
                "api_key_secret": "...",  # Reference to secret manager
                ...
            }
        """
        self.config = config
        self.model_id = config.get("model_id", "unknown")
        self.provider = config.get("provider", "unknown")
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify model is reachable and authorized.
        
        Returns:
            True if healthy, False if unreachable
        """
        pass
    
    @abstractmethod
    def execute(self, request: AdapterRequest) -> AdapterResponse:
        """
        Call the model and return response.
        
        Args:
            request: Task + configuration
            
        Returns:
            AdapterResponse with full response + metrics
            
        Raises:
            AdapterError: If request fails
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, request: AdapterRequest) -> float:
        """
        Estimate cost for this request WITHOUT executing it.
        Used for budget checks before queuing.
        
        Args:
            request: Task
            
        Returns:
            Estimated cost in USD (float)
        """
        pass
    
    def get_capabilities(self) -> dict:
        """
        Return model metadata.
        
        Returns:
            {
                "model_id": "claude-3-5-sonnet",
                "provider": "anthropic",
                "max_tokens": 100000,
                "input_price_per_1k_tokens": 0.003,
                "output_price_per_1k_tokens": 0.015,
                "version": "20241022"
            }
        """
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "version": self.config.get("version", "unknown")
        }


class MockAdapter(CandidateAdapter):
    """
    Mock adapter for testing - returns canned responses, no API cost.
    Useful for POC development before real API keys are available.
    
    Supports quality_level in config for testing different model performance:
    - "high" → Scores 100/100 (all tests pass)
    - "medium" → Scores ~70/100 (most tests pass)
    - "low" → Scores ~40/100 (some tests pass)
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.quality_level = config.get("quality_level", "medium")
        logger.info(f"Initialized MockAdapter: {self.model_id} (quality: {self.quality_level})")
    
    def health_check(self) -> bool:
        """Always healthy for testing."""
        logger.debug(f"Health check: {self.model_id} - OK")
        return True
    
    def execute(self, request: AdapterRequest) -> AdapterResponse:
        """
        Return mock Java response based on task difficulty.
        
        This is a placeholder - in Week 4+, will call real APIs.
        """
        logger.info(f"Executing task {request.task_id} on {self.model_id}")
        
        # Simulate latency (50-200ms)
        latency = 50 + (hash(request.task_id) % 150)
        time.sleep(latency / 1000.0)
        
        # Mock responses based on task difficulty
        mock_responses = {
            "easy": '''public class Solution {
    public int add(int a, int b) {
        return a + b;
    }
}''',
            "medium": '''public class Solution {
    public List<Integer> twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return Arrays.asList(map.get(complement), i);
            }
            map.put(nums[i], i);
        }
        return new ArrayList<>();
    }
}''',
            "hard": '''public class Solution {
    public int longestSubstring(String s) {
        Map<Character, Integer> charIndex = new HashMap<>();
        int maxLen = 0;
        int start = 0;
        
        for (int end = 0; end < s.length(); end++) {
            char c = s.charAt(end);
            if (charIndex.containsKey(c) && charIndex.get(c) >= start) {
                start = charIndex.get(c) + 1;
            }
            charIndex.put(c, end);
            maxLen = Math.max(maxLen, end - start + 1);
        }
        return maxLen;
    }
}'''
        }
        
        # Pick response based on task_id
        if "001" in request.task_id or "002" in request.task_id:
            response = mock_responses["easy"]
        elif "003" in request.task_id or "004" in request.task_id:
            response = mock_responses["medium"]
        else:
            response = mock_responses["hard"]
        
        return AdapterResponse(
            task_id=request.task_id,
            response=response,
            input_tokens=200,
            output_tokens=150,
            latency_ms=latency,
            status="success"
        )
    
    def estimate_cost(self, request: AdapterRequest) -> float:
        """Mock adapter costs nothing."""
        return 0.0


class OpenAIAdapter(CandidateAdapter):
    """
    OpenAI adapter for GPT-4, GPT-4o via OpenAI API.
    
    Config required:
        {
            "model_id": "gpt-4",
            "api_key_secret": "openai_api_key",
            "api_endpoint": "https://api.openai.com/v1",
            "temperature": 0.7,
            "max_tokens": 2048,
            "input_price_per_1k_tokens": 0.01,
            "output_price_per_1k_tokens": 0.03
        }
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        # In real implementation, load API key from secret manager
        self.api_key = config.get("api_key_secret", "mock_key")
        self.endpoint = config.get("api_endpoint", "https://api.openai.com/v1")
        logger.info(f"Initialized OpenAIAdapter: {self.model_id}")
    
    def health_check(self) -> bool:
        """Check if OpenAI API is reachable."""
        try:
            # In real implementation, call /models endpoint
            logger.debug(f"Health check: {self.model_id} - OK (mocked)")
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.model_id}: {str(e)}")
            return False
    
    def execute(self, request: AdapterRequest) -> AdapterResponse:
        """
        Call OpenAI API.
        
        Real implementation would:
            1. Construct messages
            2. Call OpenAI /v1/chat/completions
            3. Extract tokens from response.usage
            4. Return AdapterResponse
        """
        logger.info(f"Executing task {request.task_id} on {self.model_id}")
        
        # This is a placeholder
        # Real implementation calls OpenAI API
        raise NotImplementedError(
            "OpenAI adapter not yet implemented. "
            "Use MockAdapter for testing, or add real implementation with API key."
        )
    
    def estimate_cost(self, request: AdapterRequest) -> float:
        """Estimate cost for OpenAI request."""
        # Rough estimate: problem_statement ~200 tokens input, response ~150 output
        input_tokens = 200
        output_tokens = 150
        
        input_price = self.config.get("input_price_per_1k_tokens", 0.01)
        output_price = self.config.get("output_price_per_1k_tokens", 0.03)
        
        cost = (input_tokens * input_price / 1000) + (output_tokens * output_price / 1000)
        return cost


class AnthropicAdapter(CandidateAdapter):
    """
    Anthropic adapter for Claude via Anthropic API.
    
    Config required:
        {
            "model_id": "claude-3-5-sonnet-20241022",
            "api_key_secret": "anthropic_api_key",
            "api_endpoint": "https://api.anthropic.com/v1",
            "temperature": 0.7,
            "max_tokens": 2048,
            "input_price_per_1k_tokens": 0.003,
            "output_price_per_1k_tokens": 0.015
        }
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key_secret", "mock_key")
        self.endpoint = config.get("api_endpoint", "https://api.anthropic.com/v1")
        logger.info(f"Initialized AnthropicAdapter: {self.model_id}")
    
    def health_check(self) -> bool:
        """Check if Anthropic API is reachable."""
        try:
            logger.debug(f"Health check: {self.model_id} - OK (mocked)")
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.model_id}: {str(e)}")
            return False
    
    def execute(self, request: AdapterRequest) -> AdapterResponse:
        """
        Call Anthropic API.
        
        Real implementation would:
            1. Construct message
            2. Call Anthropic /messages endpoint
            3. Extract tokens from response.usage
            4. Return AdapterResponse
        """
        logger.info(f"Executing task {request.task_id} on {self.model_id}")
        
        # This is a placeholder
        raise NotImplementedError(
            "Anthropic adapter not yet implemented. "
            "Use MockAdapter for testing, or add real implementation with API key."
        )
    
    def estimate_cost(self, request: AdapterRequest) -> float:
        """Estimate cost for Anthropic request."""
        input_tokens = 200
        output_tokens = 150
        
        input_price = self.config.get("input_price_per_1k_tokens", 0.003)
        output_price = self.config.get("output_price_per_1k_tokens", 0.015)
        
        cost = (input_tokens * input_price / 1000) + (output_tokens * output_price / 1000)
        return cost


class LocalInferenceAdapter(CandidateAdapter):
    """
    Local inference adapter for Llama, Mistral via local server.
    Assumes ollama or vLLM running on localhost:8001
    
    Config required:
        {
            "model_id": "llama2:70b",
            "api_endpoint": "http://localhost:8001",
            "temperature": 0.7,
            "max_tokens": 2048
        }
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.endpoint = config.get("api_endpoint", "http://localhost:8001")
        logger.info(f"Initialized LocalInferenceAdapter: {self.model_id}")
    
    def health_check(self) -> bool:
        """Check if local inference server is reachable."""
        try:
            logger.debug(f"Health check: {self.model_id} - OK (mocked)")
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.model_id}: {str(e)}")
            return False
    
    def execute(self, request: AdapterRequest) -> AdapterResponse:
        """
        Call local inference server.
        
        Real implementation would:
            1. Call local server (ollama, vLLM, etc.)
            2. Extract response and tokens
            3. Return AdapterResponse
        """
        logger.info(f"Executing task {request.task_id} on {self.model_id}")
        
        raise NotImplementedError(
            "Local inference adapter not yet implemented. "
            "Use MockAdapter for testing, or set up local inference server."
        )
    
    def estimate_cost(self, request: AdapterRequest) -> float:
        """Local inference costs nothing (compute cost not tracked)."""
        return 0.0


def get_adapter(candidate_config: dict) -> CandidateAdapter:
    """
    Factory function to get the right adapter based on provider.
    
    Args:
        candidate_config: Config dict with "provider" key
        
    Returns:
        Adapter instance
    """
    provider = candidate_config.get("provider", "mock").lower()
    
    if provider == "mock":
        return MockAdapter(candidate_config)
    elif provider == "openai":
        return OpenAIAdapter(candidate_config)
    elif provider == "anthropic":
        return AnthropicAdapter(candidate_config)
    elif provider == "local":
        return LocalInferenceAdapter(candidate_config)
    else:
        logger.warning(f"Unknown provider {provider}, defaulting to MockAdapter")
        return MockAdapter(candidate_config)