from typing import Generator
from sqlalchemy.orm import Session
from app.infrastructure.database import SessionLocal
from app.domain.benchmarks.repository import BenchmarkRepository
from app.domain.benchmarks.service import BenchmarkService

def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_benchmark_service(db: Session = Depends(get_db)) -> BenchmarkService:
    """Benchmark service dependency"""
    repository = BenchmarkRepository(db)
    return BenchmarkService(repository)