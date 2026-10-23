"""Adapter providers."""

class MockAdapter:
    """Mock adapter for testing."""
    
    async def execute(self, input_data: str) -> str:
        """Execute mock task."""
        return input_data  # Just echo input as output


def get_adapter(candidate_id: str):
    """Get adapter for candidate ID."""
    if candidate_id == "mock":
        return MockAdapter()
    
    # Default to mock
    return MockAdapter()