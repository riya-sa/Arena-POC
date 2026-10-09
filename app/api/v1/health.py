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
from app.domain.candidates import \
    CandidateRepository  # Reuse from earlier file
from app.domain.candidates.service import CandidateService
from app.domain.experiments import (Execution, ExecutionStatus, Experiment,
                                    ExperimentStatus)
from app.domain.experiments.service import (ExperimentRepository,
                                            ExperimentService)
from app.domain.shared.exceptions import ArenaException

logger = get_logger(__name__)

# ============================================================================
# Health Endpoint
# ============================================================================

health_router = APIRouter(tags=["health"])


@health_router.get("/health", summary="Health check")
async def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


from datetime import datetime
