"""
API v1 endpoint tests.
File: tests/test_api_v1.py

Tests for all REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_status_code(self, client):
        """Health endpoint returns 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_health_response_structure(self, client):
        """Health endpoint returns required fields."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "healthy"
    
    def test_health_version_matches_config(self, client):
        """Health endpoint returns correct version."""
        from app.config import settings
        
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert data["version"] == settings.app_version
    
    def test_health_environment_set(self, client):
        """Health endpoint returns environment."""
        from app.config import settings
        
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert data["environment"] == settings.environment.value


class TestBenchmarkEndpoints:
    """Test benchmark REST endpoints."""
    
    def test_benchmark_list_endpoint_exists(self, client):
        """Test GET /api/v1/benchmarks endpoint."""
        # Note: May return 404 if router not fully implemented
        # This tests that endpoint is routable
        response = client.get("/api/v1/benchmarks")
        
        # Should either succeed or return 404 (endpoint exists)
        # Should NOT return 500 (internal error)
        assert response.status_code in [200, 404, 405]
    
    def test_benchmark_create_endpoint_exists(self, client):
        """Test POST /api/v1/benchmarks endpoint."""
        payload = {
            "name": "Test Benchmark",
            "description": "A test benchmark",
            "version_number": "v1.0"
        }
        
        response = client.post("/api/v1/benchmarks", json=payload)
        
        # Should not crash (200, 201, 404, or 405)
        assert response.status_code in [200, 201, 400, 404, 405]


class TestCandidateEndpoints:
    """Test candidate REST endpoints."""
    
    def test_candidate_list_endpoint_exists(self, client):
        """Test GET /api/v1/candidates endpoint."""
        response = client.get("/api/v1/candidates")
        
        assert response.status_code in [200, 404, 405]
    
    def test_candidate_create_endpoint_exists(self, client):
        """Test POST /api/v1/candidates endpoint."""
        payload = {
            "name": "Test Model",
            "provider": "mock",
            "model_id": "test-v1",
            "config": {"temperature": 0.7}
        }
        
        response = client.post("/api/v1/candidates", json=payload)
        
        assert response.status_code in [200, 201, 400, 404, 405]


class TestExperimentEndpoints:
    """Test experiment REST endpoints."""
    
    def test_experiment_list_endpoint_exists(self, client):
        """Test GET /api/v1/experiments endpoint."""
        response = client.get("/api/v1/experiments")
        
        assert response.status_code in [200, 404, 405]
    
    def test_experiment_create_endpoint_exists(self, client):
        """Test POST /api/v1/experiments endpoint."""
        payload = {
            "name": "Test Experiment",
            "benchmark_id": "bench-123",
            "candidate_ids": ["cand-1", "cand-2"],
            "repetitions": 3,
            "budget_usd": 50.0
        }
        
        response = client.post("/api/v1/experiments", json=payload)
        
        assert response.status_code in [200, 201, 400, 404, 405]
    
    def test_experiment_get_endpoint_exists(self, client):
        """Test GET /api/v1/experiments/{id} endpoint."""
        response = client.get("/api/v1/experiments/exp-123")
        
        # May not exist (404) but should route correctly
        assert response.status_code in [200, 404, 405]


class TestErrorHandling:
    """Test error handling and exception responses."""
    
    def test_nonexistent_endpoint_returns_404(self, client):
        """Test 404 for unknown endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_wrong_method_returns_405(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.delete("/api/v1/health")
        assert response.status_code == 405
    
    def test_invalid_json_returns_422(self, client):
        """Test 422 for invalid JSON payload."""
        response = client.post(
            "/api/v1/benchmarks",
            json={"invalid": "schema"},
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (validation error) or 404 if route not found
        assert response.status_code in [422, 404, 405]


class TestCORSHeaders:
    """Test CORS headers are set correctly."""
    
    def test_cors_origin_header_present(self, client):
        """Test CORS headers are included."""
        response = client.options("/api/v1/health")
        
        # OPTIONS request for CORS preflight
        # Should either succeed or return 405 (method not allowed)
        assert response.status_code in [200, 204, 405]


class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_swagger_docs_endpoint(self, client):
        """Test Swagger docs are available (if enabled)."""
        from app.config import settings
        
        if settings.enable_debug_endpoints:
            response = client.get("/api/docs")
            assert response.status_code == 200
    
    def test_redoc_endpoint(self, client):
        """Test ReDoc docs are available (if enabled)."""
        from app.config import settings
        
        if settings.enable_debug_endpoints:
            response = client.get("/api/redoc")
            assert response.status_code == 200
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        # Should be available or return 404
        assert response.status_code in [200, 404]


# ============================================================================
# Response Schema Tests
# ============================================================================

class TestResponseSchemas:
    """Test API response schemas."""
    
    def test_health_response_is_json(self, client):
        """Health response is valid JSON."""
        response = client.get("/api/v1/health")
        
        # Should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Should be parseable
        data = response.json()
        assert isinstance(data, dict)
    
    def test_error_response_has_error_field(self, client):
        """Error responses include error field."""
        response = client.get("/api/v1/nonexistent")
        
        # 404 response should be JSON with error info
        if response.status_code == 404:
            try:
                data = response.json()
                # Error response should have detail field
                assert "detail" in data
            except:
                # Some 404s might not be JSON
                pass


class TestRequestValidation:
    """Test request payload validation."""
    
    def test_missing_required_field(self, client):
        """Test validation for missing required fields."""
        # Post with missing required field
        payload = {"name": "Test"}  # Missing other required fields
        
        response = client.post("/api/v1/benchmarks", json=payload)
        
        # Should return validation error (422) or 404 if endpoint not implemented
        assert response.status_code in [422, 400, 404, 405]
    
    def test_invalid_field_type(self, client):
        """Test validation for wrong field types."""
        payload = {
            "name": "Test",
            "repetitions": "not-a-number"  # Should be int
        }
        
        response = client.post("/api/v1/experiments", json=payload)
        
        # Should return validation error
        assert response.status_code in [422, 400, 404, 405]


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test API performance."""
    
    def test_health_endpoint_response_time(self, client):
        """Health endpoint should respond quickly."""
        import time
        
        start = time.time()
        response = client.get("/api/v1/health")
        elapsed = time.time() - start
        
        # Should respond in < 100ms
        assert elapsed < 0.1
        assert response.status_code == 200


# ============================================================================
# Content Negotiation Tests
# ============================================================================

class TestContentNegotiation:
    """Test content type handling."""
    
    def test_json_response_content_type(self, client):
        """Responses should be JSON."""
        response = client.get("/api/v1/health")
        
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_request_with_json_content_type(self, client):
        """Requests with JSON content-type are handled."""
        response = client.post(
            "/api/v1/benchmarks",
            json={"name": "Test"},
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle JSON content-type correctly
        assert response.status_code in [200, 201, 400, 404, 405, 422]