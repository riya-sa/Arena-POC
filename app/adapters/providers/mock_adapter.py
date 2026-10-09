import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app import get_logger
from app.adapters.providers.base import (AdapterRequest, AdapterResponse,
                                         CandidateAdapter)
from app.domain.shared.exceptions import (AdapterAuthError, AdapterConfigError,
                                          AdapterError, AdapterRateLimitError,
                                          AdapterTimeoutError)

logger = get_logger(__name__)

# ============================================================================
# Mock Adapter (Testing)
# ============================================================================


class MockAdapter(CandidateAdapter):
    """
    Mock adapter for testing.
    Returns deterministic responses based on task difficulty.

    Config:
        {
            "quality_level": "high|medium|low",
            "model_id": "mock-model",
            "provider": "mock"
        }
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.quality_level = config.get("quality_level", "medium")
        logger.info(
            f"MockAdapter initialized: {self.model_id} (quality: {self.quality_level})"
        )

    def health_check(self) -> bool:
        """Always healthy for testing."""
        return True

    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """Return mock Java response."""
        logger.info(f"MockAdapter executing task: {request.task_id}")

        # Simulate latency
        latency = 50 + (hash(request.task_id) % 150)
        await asyncio.sleep(latency / 1000.0)

        # Mock responses
        mock_responses = {
            "easy": "public class Solution { public int add(int a, int b) { return a + b; } }",
            "medium": "public class Solution { public List<Integer> twoSum(int[] nums, int target) { /* implementation */ } }",
            "hard": "public class Solution { public int longestSubstring(String s) { /* complex impl */ } }",
        }

        response_text = mock_responses.get("medium", mock_responses["easy"])

        return AdapterResponse(
            task_id=request.task_id,
            response=response_text,
            input_tokens=200,
            output_tokens=150,
            latency_ms=latency,
            status="success",
        )

    def estimate_cost(self, request: AdapterRequest) -> float:
        """Mock costs nothing."""
        return 0.0
