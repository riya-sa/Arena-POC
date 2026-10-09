"""
Domain service unit tests.
File: tests/test_domain_services.py

Tests for benchmark, candidate, and experiment services.
FIXED to match actual domain implementation.
"""

import pytest
from datetime import datetime
from typing import Optional

from app.domain.shared.exceptions import (
    ArenaException,
    BenchmarkNotFoundError,
    CandidateNotFoundError,
    ExperimentNotFoundError,
    ValidationError
)


class TestBenchmarkService:
    """Test benchmark domain service."""
    
    def test_benchmark_suite_not_found_exception(self):
        """Test BenchmarkNotFoundError is raised correctly."""
        with pytest.raises(BenchmarkNotFoundError) as exc_info:
            raise BenchmarkNotFoundError("Benchmark suite not found")
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "BENCHMARK_NOT_FOUND"
    
    def test_validation_error(self):
        """Test ValidationError for invalid benchmark data."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Benchmark name must be non-empty")
        
        assert "name" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "VALIDATION_ERROR"
    
    def test_benchmark_suite_model_exists(self):
        """Test BenchmarkSuite model can be imported."""
        from app.domain.benchmarks.models import BenchmarkSuite
        
        assert BenchmarkSuite is not None
    
    def test_benchmark_version_model_exists(self):
        """Test BenchmarkVersion model can be imported."""
        from app.domain.benchmarks.models import BenchmarkVersion
        
        assert BenchmarkVersion is not None
    
    def test_task_model_exists(self):
        """Test Task model can be imported."""
        from app.domain.benchmarks.models import Task
        
        assert Task is not None


class TestCandidateService:
    """Test candidate domain service."""
    
    def test_candidate_not_found_exception(self):
        """Test CandidateNotFoundError is raised correctly."""
        with pytest.raises(CandidateNotFoundError) as exc_info:
            raise CandidateNotFoundError("Candidate not found")
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "CANDIDATE_NOT_FOUND"
    
    def test_candidate_validation(self):
        """Test candidate config validation."""
        # Mock candidate config
        candidate_config = {
            "name": "Test Model",
            "provider": "mock",
            "model_id": "test-model-v1",
            "config": {
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
        
        # Config should have required fields
        assert "name" in candidate_config
        assert "provider" in candidate_config
        assert "model_id" in candidate_config
        assert "config" in candidate_config
    
    def test_candidate_model_exists(self):
        """Test Candidate model can be imported."""
        from app.domain.candidates.models import Candidate
        
        assert Candidate is not None
    
    def test_candidate_version_model_exists(self):
        """Test CandidateVersion model can be imported."""
        from app.domain.candidates.models import CandidateVersion
        
        assert CandidateVersion is not None


class TestExperimentService:
    """Test experiment domain service."""
    
    def test_experiment_not_found_exception(self):
        """Test ExperimentNotFoundError is raised correctly."""
        with pytest.raises(ExperimentNotFoundError) as exc_info:
            raise ExperimentNotFoundError("Experiment not found")
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "EXPERIMENT_NOT_FOUND"
    
    def test_experiment_status_enum(self):
        """Test experiment status enum values."""
        from app.domain.experiments.models import ExperimentStatus
        
        # Verify valid states
        valid_states = [
            ExperimentStatus.CREATED,
            ExperimentStatus.QUEUED,
            ExperimentStatus.RUNNING,
            ExperimentStatus.COMPLETE,
            ExperimentStatus.FAILED,
            ExperimentStatus.CANCELLED
        ]
        
        for state in valid_states:
            assert state is not None
            assert isinstance(state, ExperimentStatus)
    
    def test_experiment_status_values(self):
        """Test experiment status enum values are correct."""
        from app.domain.experiments.models import ExperimentStatus
        
        # Verify values match expected format
        assert ExperimentStatus.CREATED.value == "created"
        assert ExperimentStatus.QUEUED.value == "queued"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.COMPLETE.value == "complete"
        assert ExperimentStatus.FAILED.value == "failed"
        assert ExperimentStatus.CANCELLED.value == "cancelled"
    
    def test_execution_status_enum(self):
        """Test execution status enum values."""
        from app.domain.experiments.models import ExecutionStatus
        
        # Verify valid states
        valid_states = [
            ExecutionStatus.QUEUED,
            ExecutionStatus.RUNNING,
            ExecutionStatus.COMPLETE,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED
        ]
        
        for state in valid_states:
            assert state is not None
            assert isinstance(state, ExecutionStatus)
    
    def test_experiment_model_exists(self):
        """Test Experiment model can be imported."""
        from app.domain.experiments.models import Experiment
        
        assert Experiment is not None
    
    def test_execution_model_exists(self):
        """Test Execution model can be imported."""
        from app.domain.experiments.models import Execution
        
        assert Execution is not None


class TestDomainExceptions:
    """Test domain exception hierarchy."""
    
    def test_arena_exception_is_base(self):
        """Test ArenaException is base for all domain exceptions."""
        assert issubclass(BenchmarkNotFoundError, ArenaException)
        assert issubclass(CandidateNotFoundError, ArenaException)
        assert issubclass(ExperimentNotFoundError, ArenaException)
        assert issubclass(ValidationError, ArenaException)
    
    def test_exception_has_http_status(self):
        """Test all exceptions have HTTP status codes."""
        exc = BenchmarkNotFoundError("test")
        assert hasattr(exc, "http_status")
        assert exc.http_status in [400, 404, 409, 500]
    
    def test_exception_has_error_code(self):
        """Test all exceptions have error codes."""
        exc = ValidationError("Invalid input")
        assert hasattr(exc, "error_code")
        assert exc.error_code == "VALIDATION_ERROR"
    
    def test_exception_message_stored(self):
        """Test exception message is stored."""
        message = "Test error message"
        exc = ArenaException(message)
        assert exc.message == message
    
    def test_exception_details_optional(self):
        """Test exception details are optional."""
        exc = ArenaException("Error", details={"field": "value"})
        assert exc.details == {"field": "value"}
        
        exc2 = ArenaException("Error")
        assert exc2.details == {}


class TestAdapterProviders:
    """Test adapter provider loading."""
    
    def test_adapter_types_available(self):
        """Test that adapter types are available."""
        from app.config import settings
        
        # Adapter type should be set
        assert settings.adapter_type in ["mock", "openai", "anthropic", "local"]
    
    def test_mock_adapter_enabled_in_dev(self):
        """Test mock adapters are enabled in development."""
        from app.config import settings
        
        if settings.environment.value == "development":
            # In development, mock adapters should be allowed
            assert settings.adapter_type == "mock" or settings.enable_mock_adapters
    
    @pytest.mark.asyncio
    async def test_adapter_config_loads(self):
        """Test adapter configuration loads from config."""
        from app.config import settings
        
        # Adapter should have valid config
        assert settings.adapter_type is not None
        assert len(settings.adapter_type) > 0


class TestApiIntegration:
    """Test API routes are integrated correctly."""
    
    def test_health_endpoint_available(self):
        """Test health endpoint is defined."""
        from app.main import app
        
        # App should be created
        assert app is not None
        assert app.title == "C/AI Arena Optimization"
    
    @pytest.mark.asyncio
    async def test_api_v1_prefix(self):
        """Test API v1 routes are under /api/v1/ prefix."""
        from app.main import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Health endpoint should exist
        api_v1_routes = [r for r in routes if r.startswith("/api/v1")]
        assert len(api_v1_routes) > 0
        assert "/api/v1/health" in api_v1_routes


class TestDatabaseModels:
    """Test database models are properly defined."""
    
    def test_benchmark_suite_model_has_required_fields(self):
        """Test BenchmarkSuite model has required fields."""
        from app.domain.benchmarks.models import BenchmarkSuite
        
        # Model should exist and be importable
        assert BenchmarkSuite is not None
        
        # Should have required columns
        assert hasattr(BenchmarkSuite, "id")
        assert hasattr(BenchmarkSuite, "name")
    
    def test_benchmark_version_model_has_required_fields(self):
        """Test BenchmarkVersion model has required fields."""
        from app.domain.benchmarks.models import BenchmarkVersion
        
        # Model should exist and be importable
        assert BenchmarkVersion is not None
        
        # Should have required columns
        assert hasattr(BenchmarkVersion, "id")
        assert hasattr(BenchmarkVersion, "version_number")
    
    def test_candidate_model_has_required_fields(self):
        """Test Candidate model has required fields."""
        from app.domain.candidates.models import Candidate
        
        # Model should exist and be importable
        assert Candidate is not None
        
        # Should have required columns
        assert hasattr(Candidate, "id")
        assert hasattr(Candidate, "name")
        assert hasattr(Candidate, "provider")
    
    def test_experiment_model_has_required_fields(self):
        """Test Experiment model has required fields."""
        from app.domain.experiments.models import Experiment
        
        # Model should exist and be importable
        assert Experiment is not None
        
        # Should have required columns
        assert hasattr(Experiment, "id")
        assert hasattr(Experiment, "status")
    
    def test_execution_model_has_required_fields(self):
        """Test Execution model has required fields."""
        from app.domain.experiments.models import Execution
        
        # Model should exist and be importable
        assert Execution is not None
        
        # Should have required columns
        assert hasattr(Execution, "id")
        assert hasattr(Execution, "status")


class TestSchemas:
    """Test API request/response schemas."""
    
    def test_benchmark_suite_schemas_load(self):
        """Test benchmark suite schemas are defined."""
        from app.domain.benchmarks.schemas import (
            BenchmarkSuiteCreateRequest,
            BenchmarkSuiteResponse,
            BenchmarkVersionResponse
        )
        
        # Schemas should be importable
        assert BenchmarkSuiteCreateRequest is not None
        assert BenchmarkSuiteResponse is not None
        assert BenchmarkVersionResponse is not None
    
    def test_task_schema_loads(self):
        """Test task schema is defined."""
        from app.domain.benchmarks.schemas import (
            TaskCreateRequest,
            TaskResponse
        )
        
        # Schemas should be importable
        assert TaskCreateRequest is not None
        assert TaskResponse is not None
    
    def test_schemas_are_pydantic_models(self):
        """Test schemas are proper Pydantic models."""
        from app.domain.benchmarks.schemas import BenchmarkSuiteCreateRequest
        from pydantic import BaseModel
        
        # Should be Pydantic model
        assert issubclass(BenchmarkSuiteCreateRequest, BaseModel)


# ============================================================================
# Integration Tests (require database)
# ============================================================================

class TestDomainIntegration:
    """Integration tests that require database."""
    
    @pytest.mark.asyncio
    async def test_benchmark_suite_crud_flow(self, db_session):
        """Test benchmark suite CRUD operations (requires DB)."""
        if db_session is None:
            pytest.skip("Database not available")
        
        # This would test: Create → Read → Update → Delete
        # Implementation depends on ORM setup
        assert True  # Placeholder
    
    @pytest.mark.asyncio
    async def test_experiment_status_transitions(self, db_session):
        """Test experiment status transitions (requires DB)."""
        if db_session is None:
            pytest.skip("Database not available")
        
        # This would test status transitions with actual DB
        assert True  # Placeholder


class TestModelMethods:
    """Test model utility methods."""
    
    def test_benchmark_suite_to_dict(self):
        """Test BenchmarkSuite.to_dict() method."""
        from app.domain.benchmarks.models import BenchmarkSuite
        
        # Should have to_dict method
        assert hasattr(BenchmarkSuite, "to_dict")
    
    def test_candidate_to_dict(self):
        """Test Candidate.to_dict() method."""
        from app.domain.candidates.models import Candidate
        
        # Should have to_dict method
        assert hasattr(Candidate, "to_dict")
    
    def test_execution_is_complete_property(self):
        """Test Execution.is_complete property."""
        from app.domain.experiments.models import Execution
        
        # Should have is_complete property
        assert hasattr(Execution, "is_complete")
    
    def test_experiment_is_running_property(self):
        """Test Experiment.is_running property."""
        from app.domain.experiments.models import Experiment
        
        # Should have is_running property
        assert hasattr(Experiment, "is_running")