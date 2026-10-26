import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app import get_logger
from app.adapters.providers import AnthropicAdapter
from app.adapters.providers import CandidateAdapter
from app.adapters.providers import LocalInferenceAdapter
from app.adapters.providers import MockAdapter
from app.adapters.providers import OpenAIAdapter
from app.domain.shared.exceptions import (AdapterAuthError, AdapterConfigError,
                                          AdapterError, AdapterRateLimitError,
                                          AdapterTimeoutError)

logger = get_logger(__name__)

# ============================================================================
# Factory
# ============================================================================


def get_adapter(config: dict) -> CandidateAdapter:
    """
    Factory function to create adapter instance.

    Args:
        config: Adapter configuration dict with "provider" key

    Returns:
        Configured adapter instance

    Raises:
        AdapterConfigError: If provider not found or config invalid
    """
    provider = config.get("provider", "mock").lower()

    adapters = {
        "mock": MockAdapter,
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "local": LocalInferenceAdapter,
    }

    adapter_class = adapters.get(provider)
    if not adapter_class:
        logger.warning(f"Unknown provider {provider}, defaulting to MockAdapter")
        return MockAdapter(config)

    try:
        return adapter_class(config)
    except Exception as e:
        raise AdapterConfigError(f"Failed to initialize {provider} adapter: {str(e)}")


import asyncio  # Import at end to avoid circular dependency
