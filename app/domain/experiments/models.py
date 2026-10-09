"""
Experiments domain: models, repository, service, and state machine.
Files:
  - app/domain/experiments/models.py
  - app/domain/experiments/state_machine.py
  - app/domain/experiments/repository.py
  - app/domain/experiments/service.py
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (DECIMAL, JSON, Boolean, Column, DateTime, ForeignKey,
                        Index, Integer, String, Text, desc, select)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.shared.exceptions import (ExecutionNotFoundError,
                                          ExperimentInvalidStateError,
                                          ExperimentNotFoundError,
                                          InsufficientBudgetError,
                                          ValidationError)
from app.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================


class ExecutionStatus(str, Enum):
    """Execution status states."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExperimentStatus(str, Enum):
    """Experiment status states."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Models
# ============================================================================


class Experiment(Base):
    """
    Benchmark experiment aggregate root.
    Represents a run of tasks against one or more candidates.
    """

    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benchmark_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benchmark_versions.id"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=True)
    status = Column(
        String(50), nullable=False, default=ExperimentStatus.CREATED.value, index=True
    )
    repetitions = Column(Integer, nullable=False, default=1)
    budget_usd = Column(DECIMAL(10, 2), nullable=True)
    spent_usd = Column(DECIMAL(10, 2), nullable=False, default=0)

    # Timestamps
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    executions = relationship(
        "Execution",
        back_populates="experiment",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_experiments_status", "status"),
        Index("ix_experiments_submitted_at", "submitted_at"),
    )

    def __repr__(self):
        return f"<Experiment(id={self.id}, status={self.status})>"

    @property
    def is_running(self) -> bool:
        return self.status in [
            ExperimentStatus.QUEUED.value,
            ExperimentStatus.RUNNING.value,
        ]

    @property
    def is_complete(self) -> bool:
        return self.status in [
            ExperimentStatus.COMPLETE.value,
            ExperimentStatus.FAILED.value,
        ]


class Execution(Base):
    """
    Individual task-candidate execution within an experiment.
    Represents running one task on one candidate version once.
    """

    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(
        UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False, index=True
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    candidate_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate_versions.id"),
        nullable=False,
        index=True,
    )

    # Which repetition (1, 2, 3, etc.)
    repetition_number = Column(Integer, nullable=False)

    # Execution state
    status = Column(
        String(50), nullable=False, default=ExecutionStatus.QUEUED.value, index=True
    )

    # Timestamps
    enqueued_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Telemetry (populated after execution)
    latency_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost_usd = Column(DECIMAL(10, 4), nullable=True)

    # Model response
    model_response = Column(Text, nullable=True)  # Full model output

    # Evaluation results (populated by evaluator)
    passed = Column(Boolean, nullable=True)
    score = Column(Integer, nullable=True)  # 0-100
    evaluation_details = Column(JSON, nullable=True)  # Detailed eval results

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    experiment = relationship("Experiment", back_populates="executions", lazy="select")
    task = relationship("Task", lazy="select")
    candidate_version = relationship("CandidateVersion", lazy="select")

    __table_args__ = (
        Index("ix_executions_experiment_status", "experiment_id", "status"),
        Index("ix_executions_status", "status"),
    )

    def __repr__(self):
        return f"<Execution(id={self.id}, status={self.status})>"

    @property
    def is_complete(self) -> bool:
        return self.status in [
            ExecutionStatus.COMPLETE.value,
            ExecutionStatus.FAILED.value,
            ExecutionStatus.TIMEOUT.value,
            ExecutionStatus.CANCELLED.value,
        ]
