"""API v1 endpoints"""

from fastapi import APIRouter
from app.api.v1 import benchmarks, candidates, experiments

router = APIRouter(prefix="/v1", tags=["v1"])

# Register all v1 routes
router.include_router(benchmarks.router)
router.include_router(candidates.router)
router.include_router(experiments.router)