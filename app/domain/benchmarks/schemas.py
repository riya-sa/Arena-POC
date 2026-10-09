"""
Benchmark domain Pydantic schemas.
File: app/domain/benchmarks/schemas.py

FIXED: Using Pydantic v2 ConfigDict instead of class Config
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# Request Schemas
# ============================================================================

class TaskCreateRequest(BaseModel):
    """Request to create a task."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "java-001",
                "problem_statement": "Implement two-sum algorithm...",
                "category": "arrays",
                "difficulty": 2,
                "public_tests": [
                    {"input": [2, 7, 11, 15], "target": 9, "expected": [0, 1]}
                ]
            }
        }
    )
    
    task_id: str = Field(..., min_length=1, description="Unique task identifier (e.g., java-001)")
    problem_statement: str = Field(..., min_length=10, description="Full problem description")
    category: Optional[str] = Field(None, description="Task category (e.g., recursion, dp)")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty 1-5 stars")
    public_tests: Optional[List[dict]] = Field(default_factory=list, description="Public test cases")


class BenchmarkSuiteCreateRequest(BaseModel):
    """Request to create a benchmark suite."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Java Coding Problems",
                "description": "Benchmark for Java coding skills"
            }
        }
    )
    
    name: str = Field(..., min_length=3, max_length=255, description="Benchmark name")
    description: Optional[str] = Field(None, max_length=1000, description="Benchmark description")


class BenchmarkVersionCreateRequest(BaseModel):
    """Request to create a new benchmark version."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version_number": "v2.0"
            }
        }
    )
    
    version_number: str = Field(..., description="Version identifier (e.g., v2.0)")


# ============================================================================
# Response Schemas
# ============================================================================

class TaskResponse(BaseModel):
    """Task in API response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    benchmark_version_id: UUID
    task_id: str
    problem_statement: str
    category: Optional[str] = None
    difficulty: Optional[int] = None
    public_tests: List[dict]
    created_at: datetime


class BenchmarkVersionResponse(BaseModel):
    """Benchmark version in API response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    suite_id: UUID
    version_number: str
    status: str  # draft, published
    published_at: Optional[datetime] = None
    created_at: datetime
    task_count: int


class BenchmarkSuiteResponse(BaseModel):
    """Benchmark suite in API response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: List[BenchmarkVersionResponse] = Field(default_factory=list)


class BenchmarkSuiteDetailResponse(BaseModel):
    """Detailed benchmark suite with all tasks."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: List[BenchmarkVersionResponse]


class BenchmarkVersionDetailResponse(BaseModel):
    """Detailed benchmark version with all tasks."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    suite_id: UUID
    version_number: str
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    task_count: int
    checksum: Optional[str] = None
    tasks: List[TaskResponse] = Field(default_factory=list)