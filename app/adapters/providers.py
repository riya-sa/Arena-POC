"""Provider factory for adapters."""

from app.adapters.providers import MockAdapter
from app.logger import logger


def get_adapter(candidate_id: str):
    """Get adapter for candidate ID."""
    logger.debug(f"Getting adapter for: {candidate_id}")
    
    if candidate_id == "mock":
        return MockAdapter()
    
    # Default to mock for now
    logger.warning(f"Adapter for {candidate_id} not found, using mock")
    return MockAdapter()