from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Benchmark, BenchmarkVersion


class BenchmarkRepository:
    """Data access layer for benchmarks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, benchmark_id: str) -> Optional[Benchmark]:
        """Retrieve benchmark by ID."""
        result = await self.db.execute(
            select(Benchmark).where(Benchmark.id == benchmark_id)
        )
        return result.scalar_one_or_none()

    async def get_version(
        self, benchmark_id: str, version: int
    ) -> Optional[BenchmarkVersion]:
        """Retrieve specific benchmark version."""
        result = await self.db.execute(
            select(BenchmarkVersion)
            .where(BenchmarkVersion.benchmark_id == benchmark_id)
            .where(BenchmarkVersion.version == version)
        )
        return result.scalar_one_or_none()

    async def create(self, benchmark: Benchmark) -> Benchmark:
        """Create new benchmark."""
        self.db.add(benchmark)
        await self.db.flush()  # Get ID without committing
        return benchmark

    async def list_by_project(self, project_id: str, skip: int = 0, limit: int = 100):
        """List benchmarks for a project."""
        result = await self.db.execute(
            select(Benchmark)
            .where(Benchmark.project_id == project_id)
            .order_by(desc(Benchmark.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
