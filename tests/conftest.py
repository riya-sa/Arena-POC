"""
Pytest configuration and fixtures.
File: tests/conftest.py
"""

import asyncio
from typing import Generator

import pytest

from app.config import settings
from app.database import Base, close_db, get_session, init_db
from app.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Event Loop (for async tests)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Logger Fixture
# ============================================================================


@pytest.fixture
def test_logger():
    """Provide logger for tests."""
    return get_logger("test")


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
async def init_test_db():
    """Initialize test database once per session."""
    logger.info("Initializing test database...")

    if settings.environment != "development":
        pytest.skip("Tests only run in development environment")

    try:
        await init_db()
        yield
        await close_db()
    except Exception as e:
        logger.error(f"Failed to initialize test database: {str(e)}")
        pytest.skip(f"Database not available: {str(e)}")


@pytest.fixture
async def db_session():
    """Provide database session for individual tests."""
    session = await get_session()

    try:
        yield session
        await session.rollback()
    finally:
        await session.close()


# ============================================================================
# Settings Fixture
# ============================================================================


@pytest.fixture
def app_settings():
    """Provide application settings for tests."""
    return settings


# ============================================================================
# Mock Adapters Fixture
# ============================================================================


@pytest.fixture
def mock_benchmark_config():
    """Mock benchmark configuration."""
    return {
        "name": "Test Benchmark",
        "description": "Test benchmark for unit tests",
        "version_number": "v1.0",
    }


@pytest.fixture
def mock_candidate_config():
    """Mock candidate configuration."""
    return {
        "name": "Test Candidate",
        "provider": "mock",
        "model_id": "test-model",
        "config": {"quality_level": "medium", "temperature": 0.7, "max_tokens": 2048},
    }


@pytest.fixture
def mock_experiment_config():
    """Mock experiment configuration."""
    return {"name": "Test Experiment", "repetitions": 2, "budget_usd": 50.0}


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest."""
    logger.info(f"Running tests in {settings.environment} environment")
    logger.info(f"Logging level: {settings.log_level}")


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Mark all async tests with asyncio marker
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================================
# Test Output
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def session_summary():
    """Print session summary."""
    logger.info("=" * 70)
    logger.info("TEST SESSION STARTED")
    logger.info(f"Environment: {settings.environment}")
    logger.info(
        f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'unknown'}"
    )
    logger.info("=" * 70)

    yield

    logger.info("=" * 70)
    logger.info("TEST SESSION COMPLETED")
    logger.info("=" * 70)
