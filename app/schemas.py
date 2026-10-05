"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# Benchmark Schemas
class TaskCreate(BaseModel):
    """Task creation request."""
    task_id: str = Field(..., description="Unique task ID (e.g., 'java-001')")
    problem_statement: str = Field(..., description="Problem description")
    category: Optional[str] = Field(None, description="Task category (e.g., 'recursion')")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty 1-5")
    public_tests: List[dict] = Field(default_factory=list, description="Public test cases")
    hidden_tests: List[dict] = Field(default_factory=list, description="Hidden test cases")


class TaskResponse(BaseModel):
    """Task response."""
    id: UUID
    task_id: str
    problem_statement: str
    category: Optional[str]
    difficulty: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BenchmarkSuiteCreate(BaseModel):
    """Benchmark suite creation request."""
    name: str = Field(..., description="Benchmark name")
    description: Optional[str] = Field(None, description="Benchmark description")
    tasks: List[TaskCreate] = Field(default_factory=list, description="Initial tasks")


class BenchmarkVersionResponse(BaseModel):
    """Benchmark version response."""
    id: UUID
    version_number: str
    status: str
    published_at: Optional[datetime]
    tasks: List[TaskResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class BenchmarkSuiteResponse(BaseModel):
    """Benchmark suite response."""
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    versions: List[BenchmarkVersionResponse] = []
    
    class Config:
        from_attributes = True


# Candidate Schemas
class CandidateVersionCreate(BaseModel):
    """Candidate version creation request."""
    version_number: str = Field(..., description="Version (e.g., '1.0')")
    model_id: str = Field(..., description="Model identifier (e.g., 'claude-3-5-sonnet')")
    config: dict = Field(default_factory=dict, description="Model configuration (temperature, max_tokens, etc.)")


class CandidateCreate(BaseModel):
    """Candidate creation request."""
    name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Provider (anthropic, openai, local)")
    description: Optional[str] = Field(None, description="Description")
    version: CandidateVersionCreate = Field(..., description="Initial version")


class CandidateVersionResponse(BaseModel):
    """Candidate version response."""
    id: UUID
    version_number: str
    model_id: str
    config: dict
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    """Candidate response."""
    id: UUID
    name: str
    provider: str
    description: Optional[str]
    created_at: datetime
    versions: List[CandidateVersionResponse] = []
    
    class Config:
        from_attributes = True


# Experiment Schemas
class ExperimentCreate(BaseModel):
    """Experiment creation request."""
    benchmark_version_id: UUID = Field(..., description="Benchmark version to evaluate")
    candidate_version_ids: List[UUID] = Field(..., description="Candidate versions to compare")
    name: Optional[str] = Field(None, description="Experiment name")
    repetitions: int = Field(default=1, ge=1, le=10, description="Runs per task-candidate")
    budget_usd: Optional[Decimal] = Field(None, description="Max budget")


class ExecutionResponse(BaseModel):
    """Execution response."""
    id: UUID
    status: str
    repetition_number: int
    latency_ms: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    cost_usd: Optional[Decimal]
    passed: Optional[bool]
    score: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExperimentResponse(BaseModel):
    """Experiment response."""
    id: UUID
    status: str
    name: Optional[str]
    repetitions: int
    budget_usd: Optional[Decimal]
    spent_usd: Decimal
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    executions: List[ExecutionResponse] = []
    
    class Config:
        from_attributes = True


# Status/Info Schemas
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    environment: str


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_code: Optional[str] = None