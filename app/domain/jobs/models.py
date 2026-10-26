"""Job and task queue models for distributed execution."""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
import json


class JobStatus(str, Enum):
    """Job execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Individual task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Task(BaseModel):
    """Single task in an execution."""
    id: str
    benchmark_id: str
    task_name: str
    input_data: str
    expected_output: str
    
    class Config:
        frozen = True


class Job(BaseModel):
    """Job represents a set of tasks for a candidate."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    experiment_id: str
    candidate_id: str
    candidate_name: str
    status: JobStatus = JobStatus.QUEUED
    tasks: list[Task] = Field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_json(self) -> str:
        """Serialize job to JSON for Redis storage."""
        data = self.dict()
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Job':
        """Deserialize job from JSON."""
        data = json.loads(json_str)
        # Convert datetime strings back to datetime
        if data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['started_at']:
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        # Convert task dicts to Task objects
        data['tasks'] = [Task(**t) if isinstance(t, dict) else t for t in data['tasks']]
        return cls(**data)
    
    def progress_percent(self) -> int:
        """Calculate job progress percentage."""
        if self.total_tasks == 0:
            return 0
        return int((self.completed_tasks / self.total_tasks) * 100)


class JobResult(BaseModel):
    """Result of a single task execution."""
    task_id: str
    job_id: str
    candidate_id: str
    status: TaskStatus
    output: Optional[str] = None
    score: Optional[float] = None
    execution_time_ms: float
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobQueue(BaseModel):
    """Queue item for Redis."""
    job_id: str
    experiment_id: str
    candidate_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Schemas for API
class JobSubmitRequest(BaseModel):
    """Request to submit a job."""
    experiment_id: str
    candidate_id: str
    candidate_name: str
    tasks: list[Task]


class JobResponse(BaseModel):
    """Response with job info."""
    id: str
    experiment_id: str
    candidate_id: str
    status: JobStatus
    progress_percent: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class JobDetailResponse(JobResponse):
    """Detailed job response with results."""
    tasks: list[Task]
    results: Dict[str, Any]
    error_message: Optional[str]