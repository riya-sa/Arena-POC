from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, DECIMAL, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional
from enum import Enum
import uuid

from app.database import Base
from app.domain.experiments.models import Execution, ExecutionStatus, Experiment
from app.domain.shared.exceptions import (
    ExperimentNotFoundError,
    ExecutionNotFoundError,
    ExperimentInvalidStateError,
    InsufficientBudgetError,
    ValidationError
)
from app.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Repository Layer
# ============================================================================

class ExperimentRepository:
    """Data access layer for experiments."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_experiment(self, experiment: Experiment) -> Experiment:
        """Create a new experiment."""
        self.db.add(experiment)
        await self.db.flush()
        return experiment
    
    async def get_experiment_by_id(self, experiment_id: str) -> Optional[Experiment]:
        """Retrieve experiment by ID."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        return result.scalar_one_or_none()
    
    async def list_experiments(self, skip: int = 0, limit: int = 100) -> List[Experiment]:
        """List all experiments."""
        result = await self.db.execute(
            select(Experiment)
            .order_by(desc(Experiment.submitted_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_execution(self, execution: Execution) -> Execution:
        """Create a new execution."""
        self.db.add(execution)
        await self.db.flush()
        return execution
    
    async def create_executions_bulk(self, executions: List[Execution]) -> List[Execution]:
        """Create multiple executions at once."""
        for execution in executions:
            self.db.add(execution)
        await self.db.flush()
        return executions
    
    async def get_execution_by_id(self, execution_id: str) -> Optional[Execution]:
        """Retrieve execution by ID."""
        result = await self.db.execute(
            select(Execution).where(Execution.id == execution_id)
        )
        return result.scalar_one_or_none()
    
    async def list_experiment_executions(self, experiment_id: str) -> List[Execution]:
        """List all executions in an experiment."""
        result = await self.db.execute(
            select(Execution)
            .where(Execution.experiment_id == experiment_id)
            .order_by(Execution.created_at)
        )
        return result.scalars().all()
    
    async def list_queued_executions(self, limit: int = 100) -> List[Execution]:
        """Get queued executions for worker to pick up."""
        result = await self.db.execute(
            select(Execution)
            .where(Execution.status == ExecutionStatus.QUEUED.value)
            .order_by(Execution.enqueued_at)
            .limit(limit)
        )
        return result.scalars().all()