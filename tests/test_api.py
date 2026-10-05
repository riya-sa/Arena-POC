"""
Basic API tests for C/AI Arena POC
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealth:
    """Health check tests."""
    
    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "arena-poc"
    
    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()


class TestBenchmarks:
    """Benchmark API tests."""
    
    def test_create_benchmark(self):
        """Test creating a benchmark."""
        payload = {
            "name": "Test Benchmark",
            "description": "A test benchmark",
            "tasks": [
                {
                    "task_id": "test-001",
                    "problem_statement": "Test task",
                    "category": "test",
                    "difficulty": 1,
                    "public_tests": []
                }
            ]
        }
        response = client.post("/api/v1/benchmarks", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Benchmark"
        assert len(data["versions"]) == 1
        assert data["versions"][0]["status"] == "draft"
        assert data["versions"][0]["version_number"] == "v1.0"
    
    def test_list_benchmarks(self):
        """Test listing benchmarks."""
        # Create one first
        payload = {
            "name": "Test Benchmark 2",
            "description": "Another test",
            "tasks": []
        }
        client.post("/api/v1/benchmarks", json=payload)
        
        # List them
        response = client.get("/api/v1/benchmarks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
    
    def test_get_benchmark(self):
        """Test retrieving specific benchmark."""
        # Create first
        payload = {
            "name": "Test Benchmark 3",
            "description": "Test retrieve",
            "tasks": []
        }
        create_response = client.post("/api/v1/benchmarks", json=payload)
        benchmark_id = create_response.json()["id"]
        
        # Retrieve
        response = client.get(f"/api/v1/benchmarks/{benchmark_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == benchmark_id
        assert data["name"] == "Test Benchmark 3"
    
    def test_publish_version(self):
        """Test publishing a benchmark version."""
        # Create benchmark
        payload = {
            "name": "Test Benchmark Publish",
            "description": "Test publish",
            "tasks": []
        }
        create_response = client.post("/api/v1/benchmarks", json=payload)
        benchmark_id = create_response.json()["id"]
        version_id = create_response.json()["versions"][0]["id"]
        
        # Publish version
        response = client.post(
            f"/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/publish"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None
    
    def test_cannot_publish_twice(self):
        """Test that published versions cannot be published again."""
        # Create and publish
        payload = {
            "name": "Test Double Publish",
            "description": "Test",
            "tasks": []
        }
        create_response = client.post("/api/v1/benchmarks", json=payload)
        benchmark_id = create_response.json()["id"]
        version_id = create_response.json()["versions"][0]["id"]
        
        # Publish once
        client.post(f"/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/publish")
        
        # Try to publish again
        response = client.post(
            f"/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/publish"
        )
        assert response.status_code == 400
        assert "already published" in response.json()["detail"]
    
    def test_add_tasks_to_draft(self):
        """Test adding tasks to draft version."""
        # Create benchmark
        payload = {
            "name": "Test Add Tasks",
            "description": "Test",
            "tasks": []
        }
        create_response = client.post("/api/v1/benchmarks", json=payload)
        benchmark_id = create_response.json()["id"]
        version_id = create_response.json()["versions"][0]["id"]
        
        # Add tasks
        tasks_payload = {
            "tasks": [
                {
                    "task_id": "task-001",
                    "problem_statement": "Do something",
                    "category": "test",
                    "difficulty": 2,
                    "public_tests": []
                }
            ]
        }
        response = client.post(
            f"/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/add-tasks",
            json=tasks_payload
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_id"] == "task-001"
    
    def test_cannot_add_tasks_to_published(self):
        """Test that tasks cannot be added to published versions."""
        # Create, add task, and publish
        payload = {
            "name": "Test Immutable",
            "description": "Test",
            "tasks": [
                {
                    "task_id": "task-001",
                    "problem_statement": "Do something",
                    "category": "test",
                    "difficulty": 1,
                    "public_tests": []
                }
            ]
        }
        create_response = client.post("/api/v1/benchmarks", json=payload)
        benchmark_id = create_response.json()["id"]
        version_id = create_response.json()["versions"][0]["id"]
        
        # Publish
        client.post(f"/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/publish")
        
        # Try to add task to published version
        tasks_payload = {
            "tasks": [
                {
                    "task_id": "task-002",
                    "problem_statement": "Another task",
                    "category": "test",
                    "difficulty": 1,
                    "public_tests": []
                }
            ]
        }
        response = client.post(
            f"/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/add-tasks",
            json=tasks_payload
        )
        assert response.status_code == 400
        assert "Cannot add tasks to published version" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])