"""
app/api/v1/benchmarks.py

Copy this file directly to: app/api/v1/benchmarks.py
NO EDITING NEEDED
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Optional

from app.domain.benchmarks.service import BenchmarkService
from app.infrastructure.dependencies import get_benchmark_service, get_current_user

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


class BenchmarkCreate(BaseModel):
    name: str
    description: Optional[str] = None


class BenchmarkResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    created_at: str


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BenchmarkResponse)
def create_benchmark(
    benchmark: BenchmarkCreate,
    service: BenchmarkService = Depends(get_benchmark_service),
    current_user: str = Depends(get_current_user)
):
    """Create new benchmark suite"""
    suite = service.create_suite(
        name=benchmark.name,
        description=benchmark.description,
        owner_id=current_user
    )
    return {
        "id": str(suite.id),
        "name": suite.name,
        "description": suite.description,
        "owner_id": suite.owner_id,
        "created_at": suite.created_at.isoformat()
    }


@router.get("/")
def list_benchmarks(
    service: BenchmarkService = Depends(get_benchmark_service),
    current_user: str = Depends(get_current_user)
):
    """List benchmark suites owned by current user"""
    suites = service.list_suites(current_user)
    return {
        "suites": [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "versions": len(s.versions),
                "owner_id": s.owner_id,
                "created_at": s.created_at.isoformat()
            }
            for s in suites
        ]
    }