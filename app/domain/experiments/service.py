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
from app.domain.experiments.models import (Execution, ExecutionStatus,
                                           Experiment, ExperimentStatus)
from app.domain.experiments.repository import ExperimentRepository
from app.domain.experiments.state_machine import ExperimentStateMachine
from app.domain.shared.exceptions import (ExecutionNotFoundError,
                                          ExperimentInvalidStateError,
                                          ExperimentNotFoundError,
                                          InsufficientBudgetError,
                                          ValidationError)
from app.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Service Layer
# ============================================================================


class ExperimentService:
    """Experiment business logic."""

    def __init__(self, repo: ExperimentRepository):
        self.repo = repo
        self.state_machine = ExperimentStateMachine()

    async def create_experiment(
        self,
        benchmark_version_id: str,
        tasks: List[object],  # List of Task objects
        candidate_versions: List[object],  # List of CandidateVersion objects
        repetitions: int = 1,
        budget_usd: Optional[float] = None,
        name: str = None,
    ) -> Experiment:
        """
        Create and queue a benchmark experiment.

        Creates an Execution for every (task, candidate, repetition) combination.

        Args:
            benchmark_version_id: Benchmark version to run
            tasks: List of Task objects to execute
            candidate_versions: List of CandidateVersion objects to compare
            repetitions: Number of times to repeat each task
            budget_usd: Optional budget cap
            name: Optional experiment name

        Returns:
            Created Experiment in QUEUED status

        Raises:
            ValidationError: If invalid inputs
            InsufficientBudgetError: If estimated cost exceeds budget
        """
        # Validate inputs
        if not tasks:
            raise ValidationError("Experiment must have at least one task")
        if not candidate_versions:
            raise ValidationError("Experiment must have at least one candidate")
        if repetitions < 1:
            raise ValidationError("Repetitions must be >= 1")

        # Estimate cost
        estimated_cost = self._estimate_experiment_cost(
            tasks, candidate_versions, repetitions
        )

        if budget_usd and estimated_cost > budget_usd:
            raise InsufficientBudgetError(
                f"Estimated cost ${estimated_cost:.2f} exceeds budget ${budget_usd:.2f}"
            )

        # Create experiment
        experiment = Experiment(
            benchmark_version_id=benchmark_version_id,
            name=name or f"Experiment {uuid.uuid4().hex[:8]}",
            status=ExperimentStatus.CREATED.value,
            repetitions=repetitions,
            budget_usd=budget_usd,
            spent_usd=0,
        )
        await self.repo.create_experiment(experiment)

        # Create executions (task × candidate × repetition)
        executions = []
        for task in tasks:
            for candidate_version in candidate_versions:
                for rep in range(1, repetitions + 1):
                    execution = Execution(
                        experiment_id=experiment.id,
                        task_id=task.id,
                        candidate_version_id=candidate_version.id,
                        repetition_number=rep,
                        status=ExecutionStatus.QUEUED.value,
                        enqueued_at=datetime.utcnow(),
                    )
                    executions.append(execution)

        await self.repo.create_executions_bulk(executions)

        # Move to QUEUED state
        experiment.status = ExperimentStatus.QUEUED.value

        logger.info(
            f"Created experiment: {experiment.id} "
            f"({len(tasks)} tasks × {len(candidate_versions)} candidates × {repetitions} reps = {len(executions)} executions)"
        )

        return experiment

    async def get_experiment(self, experiment_id: str) -> Experiment:
        """
        Retrieve experiment.

        Raises:
            ExperimentNotFoundError: If not found
        """
        experiment = await self.repo.get_experiment_by_id(experiment_id)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment not found: {experiment_id}")
        return experiment

    async def cancel_experiment(self, experiment_id: str) -> Experiment:
        """
        Cancel an experiment.

        Raises:
            ExperimentNotFoundError: If not found
            ExperimentInvalidStateError: If cannot transition to cancelled
        """
        experiment = await self.get_experiment(experiment_id)

        if not self.state_machine.can_transition_experiment(
            experiment.status, ExperimentStatus.CANCELLED.value
        ):
            raise ExperimentInvalidStateError(
                f"Cannot cancel experiment in state: {experiment.status}"
            )

        experiment.status = ExperimentStatus.CANCELLED.value

        # Also cancel all queued/running executions
        executions = await self.repo.list_experiment_executions(experiment_id)
        for execution in executions:
            if execution.status in [
                ExecutionStatus.QUEUED.value,
                ExecutionStatus.RUNNING.value,
            ]:
                execution.status = ExecutionStatus.CANCELLED.value

        logger.info(f"Cancelled experiment: {experiment_id}")
        return experiment

    async def update_execution_status(
        self, execution_id: str, new_status: str, **updates
    ) -> Execution:
        """
        Update execution status and metadata.

        Args:
            execution_id: Execution to update
            new_status: New status
            **updates: Additional fields (latency_ms, score, error_message, etc.)

        Raises:
            ExecutionNotFoundError: If not found
            ExperimentInvalidStateError: If invalid state transition
        """
        execution = await self.repo.get_execution_by_id(execution_id)
        if not execution:
            raise ExecutionNotFoundError(f"Execution not found: {execution_id}")

        if not self.state_machine.can_transition_execution(
            execution.status, new_status
        ):
            raise ExperimentInvalidStateError(
                f"Cannot transition execution from {execution.status} to {new_status}"
            )

        # Update status
        execution.status = new_status

        # Update provided fields
        for key, value in updates.items():
            if hasattr(execution, key):
                setattr(execution, key, value)

        # Set timestamps
        if new_status == ExecutionStatus.RUNNING.value:
            execution.started_at = datetime.utcnow()
        elif new_status in [
            ExecutionStatus.COMPLETE.value,
            ExecutionStatus.FAILED.value,
            ExecutionStatus.TIMEOUT.value,
        ]:
            execution.completed_at = datetime.utcnow()

        logger.debug(f"Updated execution {execution_id} to {new_status}")
        return execution

    async def get_queued_executions(self, limit: int = 100) -> List[Execution]:
        """
        Get executions waiting to be run.
        Used by workers to pick up jobs.
        """
        return await self.repo.list_queued_executions(limit)

    # Private helper methods

    def _estimate_experiment_cost(
        self, tasks, candidate_versions, repetitions: int
    ) -> float:
        """
        Estimate total experiment cost.
        Uses candidate config pricing if available.
        """
        # Rough estimate: $0.001 per execution
        # Real implementation would sum candidate.estimate_cost() for each
        return len(tasks) * len(candidate_versions) * repetitions * 0.001
