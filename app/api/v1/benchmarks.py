"""
API v1 handlers - thin controllers that delegate to services.
Files:
  - app/api/v1/benchmarks.py
  - app/api/v1/candidates.py
  - app/api/v1/experiments.py
"""

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


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_benchmark_service(db: AsyncSession = Depends(get_db)) -> BenchmarkService:
    """Get configured benchmark service."""
    repo = BenchmarkRepository(db)
    return BenchmarkService(repo)


# ============================================================================
# Benchmark Endpoints
# ============================================================================

benchmark_router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@benchmark_router.post(
    "/",
    response_model=BenchmarkSuiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create benchmark suite",
)
async def create_benchmark_suite(
    req: BenchmarkSuiteCreateRequest,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkSuiteResponse:
    """
    Create a new benchmark suite.

    Automatically creates v1.0 in draft status.
    """
    try:
        suite = await service.create_benchmark_suite(
            name=req.name, description=req.description
        )
        return BenchmarkSuiteResponse.from_orm(suite)
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating benchmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create benchmark",
        )


@benchmark_router.get(
    "/", response_model=List[BenchmarkSuiteResponse], summary="List benchmarks"
)
async def list_benchmarks(
    skip: int = 0,
    limit: int = 100,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> List[BenchmarkSuiteResponse]:
    """List all benchmark suites."""
    try:
        suites = await service.repo.list_suites(skip, limit)
        return [BenchmarkSuiteResponse.from_orm(s) for s in suites]
    except Exception as e:
        logger.error(f"Error listing benchmarks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list benchmarks",
        )


@benchmark_router.get(
    "/{benchmark_id}", response_model=BenchmarkSuiteResponse, summary="Get benchmark"
)
async def get_benchmark(
    benchmark_id: str, service: BenchmarkService = Depends(get_benchmark_service)
) -> BenchmarkSuiteResponse:
    """Get a specific benchmark suite."""
    try:
        suite = await service.get_suite(benchmark_id)
        return BenchmarkSuiteResponse.from_orm(suite)
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@benchmark_router.post(
    "/{benchmark_id}/versions",
    response_model=BenchmarkVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new version",
)
async def create_benchmark_version(
    benchmark_id: str,
    req: BenchmarkVersionCreateRequest,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkVersionResponse:
    """Create a new version of a benchmark suite."""
    try:
        version = await service.create_new_version(benchmark_id, req.version_number)
        return BenchmarkVersionResponse.from_orm(version)
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@benchmark_router.get(
    "/{benchmark_id}/versions/{version_id}",
    response_model=BenchmarkVersionDetailResponse,
    summary="Get version details",
)
async def get_benchmark_version(
    benchmark_id: str,
    version_id: str,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkVersionDetailResponse:
    """Get a specific benchmark version with all tasks."""
    try:
        version = await service.get_version(version_id)
        tasks = await service.repo.get_tasks_by_version(version_id)

        return BenchmarkVersionDetailResponse(
            id=version.id,
            suite_id=version.suite_id,
            version_number=version.version_number,
            status=version.status,
            published_at=version.published_at,
            created_at=version.created_at,
            task_count=version.task_count,
            checksum=version.checksum,
            tasks=[t.to_dict() for t in tasks],
        )
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@benchmark_router.post(
    "/{benchmark_id}/versions/{version_id}/tasks",
    response_model=List[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add tasks to version",
)
async def add_tasks_to_version(
    benchmark_id: str,
    version_id: str,
    tasks_req: List[TaskCreateRequest],
    service: BenchmarkService = Depends(get_benchmark_service),
) -> List[dict]:
    """Add tasks to a benchmark version (draft only)."""
    try:
        tasks_data = [t.dict() for t in tasks_req]
        tasks = await service.add_tasks(version_id, tasks_data)
        return [t.to_dict() for t in tasks]
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@benchmark_router.post(
    "/{benchmark_id}/versions/{version_id}/publish",
    response_model=BenchmarkVersionResponse,
    summary="Publish version",
)
async def publish_benchmark_version(
    benchmark_id: str,
    version_id: str,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkVersionResponse:
    """Publish a benchmark version (make immutable)."""
    try:
        version = await service.publish_version(version_id)
        return BenchmarkVersionResponse.from_orm(version)
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
