from .repository import BenchmarkRepository
from .models import Benchmark, BenchmarkVersion
from typing import Optional
from app.domain.shared.exceptions import BenchmarkNotFoundError, DataValidationError

class BenchmarkService:
    """Business logic for benchmarks."""
    
    def __init__(self, repo: BenchmarkRepository, logger):
        self.repo = repo
        self.logger = logger
    
    async def get_versioned(self, benchmark_id: str, version: Optional[int] = None):
        """Get benchmark with specific version (or latest)."""
        benchmark = await self.repo.get_by_id(benchmark_id)
        if not benchmark:
            raise BenchmarkNotFoundError(f"Benchmark {benchmark_id} not found")
        
        if version is None:
            # Get latest version
            version = await self._get_latest_version(benchmark_id)
        
        bench_version = await self.repo.get_version(benchmark_id, version)
        if not bench_version:
            raise BenchmarkNotFoundError(
                f"Benchmark {benchmark_id} version {version} not found"
            )
        
        return bench_version
    
    async def create_benchmark(self, project_id: str, name: str, description: str, created_by: str):
        """Create new benchmark."""
        if not name or len(name) < 3:
            raise DataValidationError("Benchmark name must be at least 3 characters")
        
        benchmark = Benchmark(
            project_id=project_id,
            name=name,
            description=description,
            created_by=created_by
        )
        
        self.logger.info(
            "benchmark_created",
            benchmark_id=benchmark.id,
            name=name,
            project_id=project_id
        )
        
        return await self.repo.create(benchmark)