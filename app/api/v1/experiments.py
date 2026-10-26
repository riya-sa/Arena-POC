from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import get_db, get_logger
from app.domain.benchmarks.schemas import (BenchmarkSuiteCreateRequest,
                                           BenchmarkSuiteResponse,
                                           BenchmarkVersionCreateRequest,
                                           BenchmarkVersionDetailResponse,
                                           BenchmarkVersionResponse,
                                           TaskCreateRequest)
# Domain imports
from app.domain.benchmarks.service import BenchmarkRepository, BenchmarkService
from app.domain.candidates.repository import \
    CandidateRepository  # Reuse from earlier file
from app.domain.candidates.service import CandidateService
from app.domain.experiments import (Execution, ExecutionStatus, Experiment,
                                    ExperimentStatus)
from app.domain.experiments.service import (ExperimentRepository,
                                            ExperimentService)
from app.domain.shared.exceptions import ArenaException

logger = get_logger(__name__)


async def get_experiment_service(
    db: AsyncSession = Depends(get_db),
) -> ExperimentService:
    """Get configured experiment service."""
    repo = ExperimentRepository(db)
    return ExperimentService(repo)


# ============================================================================
# Experiment Endpoints
# ============================================================================

experiment_router = APIRouter(prefix="/experiments", tags=["experiments"])


@experiment_router.post(
    "/", status_code=status.HTTP_201_CREATED, summary="Create experiment"
)
async def create_experiment(
    benchmark_version_id: str,
    candidate_version_ids: List[str],
    repetitions: int = 1,
    budget_usd: float = None,
    name: str = None,
    service: ExperimentService = Depends(get_experiment_service),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create and queue a benchmark experiment.

    Creates executions for every (task, candidate, repetition) combination.
    """
    try:
        # Import here to avoid circular dependency
        from app.domain.benchmarks.models import BenchmarkVersion, Task
        from app.domain.candidates.models import CandidateVersion

        # Fetch benchmark and tasks
        benchmark = await db.get(BenchmarkVersion, benchmark_version_id)
        if not benchmark:
            raise HTTPException(404, "Benchmark version not found")

        tasks = await service.repo.db.execute(
            "SELECT * FROM tasks WHERE benchmark_version_id = ?", [benchmark_version_id]
        )

        # Fetch candidates
        candidates = await service.repo.db.execute(
            "SELECT * FROM candidate_versions WHERE id IN (?)", [candidate_version_ids]
        )

        experiment = await service.create_experiment(
            benchmark_version_id=benchmark_version_id,
            tasks=tasks,
            candidate_versions=candidates,
            repetitions=repetitions,
            budget_usd=budget_usd,
            name=name,
        )

        return {
            "id": str(experiment.id),
            "status": experiment.status,
            "name": experiment.name,
            "repetitions": experiment.repetitions,
        }
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@experiment_router.get("/", summary="List experiments")
async def list_experiments(
    skip: int = 0,
    limit: int = 100,
    service: ExperimentService = Depends(get_experiment_service),
) -> List[dict]:
    """List all experiments."""
    try:
        experiments = await service.repo.list_experiments(skip, limit)
        return [
            {
                "id": str(e.id),
                "status": e.status,
                "name": e.name,
                "submitted_at": e.submitted_at.isoformat(),
            }
            for e in experiments
        ]
    except Exception as e:
        logger.error(f"Error listing experiments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list experiments",
        )


@experiment_router.get("/{experiment_id}", summary="Get experiment")
async def get_experiment(
    experiment_id: str, service: ExperimentService = Depends(get_experiment_service)
) -> dict:
    """Get a specific experiment."""
    try:
        experiment = await service.get_experiment(experiment_id)
        return {
            "id": str(experiment.id),
            "status": experiment.status,
            "name": experiment.name,
            "submitted_at": experiment.submitted_at.isoformat(),
            "repetitions": experiment.repetitions,
        }
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@experiment_router.post("/{experiment_id}/cancel", summary="Cancel experiment")
async def cancel_experiment(
    experiment_id: str, service: ExperimentService = Depends(get_experiment_service)
) -> dict:
    """Cancel an experiment."""
    try:
        experiment = await service.cancel_experiment(experiment_id)
        return {
            "id": str(experiment.id),
            "status": experiment.status,
            "cancelled_at": datetime.utcnow().isoformat(),
        }
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)    