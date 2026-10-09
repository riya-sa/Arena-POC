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


async def get_candidate_service(db: AsyncSession = Depends(get_db)) -> CandidateService:
    """Get configured candidate service."""
    repo = CandidateRepository(db)
    return CandidateService(repo)


# ============================================================================
# Candidate Endpoints
# ============================================================================

candidate_router = APIRouter(prefix="/candidates", tags=["candidates"])


@candidate_router.post(
    "/", status_code=status.HTTP_201_CREATED, summary="Register candidate"
)
async def register_candidate(
    name: str,
    provider: str,
    model_id: str,
    description: str = None,
    config: dict = None,
    service: CandidateService = Depends(get_candidate_service),
) -> dict:
    """Register a new model candidate."""
    try:
        candidate = await service.register_candidate(
            name=name,
            provider=provider,
            model_id=model_id,
            description=description,
            config=config,
        )
        return candidate.to_dict()
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@candidate_router.get("/", summary="List candidates")
async def list_candidates(
    skip: int = 0,
    limit: int = 100,
    service: CandidateService = Depends(get_candidate_service),
) -> List[dict]:
    """List all registered candidates."""
    try:
        candidates = await service.repo.list_candidates(skip, limit)
        return [c.to_dict() for c in candidates]
    except Exception as e:
        logger.error(f"Error listing candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list candidates",
        )


@candidate_router.get("/{candidate_id}", summary="Get candidate")
async def get_candidate(
    candidate_id: str, service: CandidateService = Depends(get_candidate_service)
) -> dict:
    """Get a specific candidate."""
    try:
        candidate = await service.get_candidate(candidate_id)
        return candidate.to_dict()
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)


@candidate_router.post("/{candidate_id}/health", summary="Check health")
async def check_candidate_health(
    candidate_id: str, service: CandidateService = Depends(get_candidate_service)
) -> dict:
    """Check if candidate is healthy and reachable."""
    try:
        candidate = await service.get_candidate(candidate_id)
        version = await service.get_active_version(candidate_id)

        # Import here to avoid circular dependency
        from app.adapters.providers.factory import get_adapter

        adapter = get_adapter(version.config)
        is_healthy = adapter.health_check()

        return {
            "candidate_id": str(candidate.id),
            "candidate_name": candidate.name,
            "healthy": is_healthy,
            "model_id": version.model_id,
            "provider": candidate.provider,
        }
    except ArenaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
