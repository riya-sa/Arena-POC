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
from app.domain.experiments.models import ExecutionStatus, ExperimentStatus
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
# State Machine
# ============================================================================

class ExperimentStateMachine:
    """
    Handles valid state transitions for experiments and executions.
    Enforces domain rules for state changes.
    """
    
    # Valid experiment status transitions
    EXPERIMENT_TRANSITIONS = {
        ExperimentStatus.CREATED.value: [ExperimentStatus.QUEUED.value, ExperimentStatus.CANCELLED.value],
        ExperimentStatus.QUEUED.value: [ExperimentStatus.RUNNING.value, ExperimentStatus.CANCELLED.value],
        ExperimentStatus.RUNNING.value: [ExperimentStatus.COMPLETE.value, ExperimentStatus.FAILED.value, ExperimentStatus.CANCELLED.value],
        ExperimentStatus.COMPLETE.value: [],
        ExperimentStatus.FAILED.value: [],
        ExperimentStatus.CANCELLED.value: [],
    }
    
    # Valid execution status transitions
    EXECUTION_TRANSITIONS = {
        ExecutionStatus.QUEUED.value: [ExecutionStatus.RUNNING.value, ExecutionStatus.CANCELLED.value],
        ExecutionStatus.RUNNING.value: [ExecutionStatus.COMPLETE.value, ExecutionStatus.FAILED.value, ExecutionStatus.TIMEOUT.value],
        ExecutionStatus.COMPLETE.value: [],
        ExecutionStatus.FAILED.value: [],
        ExecutionStatus.TIMEOUT.value: [],
        ExecutionStatus.CANCELLED.value: [],
    }
    
    @staticmethod
    def can_transition_experiment(current: str, target: str) -> bool:
        """Check if experiment can transition from current to target state."""
        if current not in ExperimentStateMachine.EXPERIMENT_TRANSITIONS:
            return False
        return target in ExperimentStateMachine.EXPERIMENT_TRANSITIONS[current]
    
    @staticmethod
    def can_transition_execution(current: str, target: str) -> bool:
        """Check if execution can transition from current to target state."""
        if current not in ExperimentStateMachine.EXECUTION_TRANSITIONS:
            return False
        return target in ExperimentStateMachine.EXECUTION_TRANSITIONS[current]