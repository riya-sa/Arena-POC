"""
app/infrastructure/dependencies.py

Copy this file directly to: app/infrastructure/dependencies.py
NO EDITING NEEDED
"""

from functools import lru_cache
from sqlalchemy.orm import Session
from fastapi import Depends, Header
from typing import Optional
from typing import Generator

from app.infrastructure.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract current user from Authorization header"""
    from app.shared.errors import AuthenticationError
    
    if not authorization:
        raise AuthenticationError("Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization format")
    
    user_id = authorization.replace("Bearer ", "").strip()
    
    if not user_id:
        raise AuthenticationError("User ID required in token")
    
    return user_id


def get_benchmark_service(db: Session = Depends(get_db)):
    """Benchmark service with injected database"""
    from app.domain.benchmarks.repository import BenchmarkRepository
    from app.domain.benchmarks.service import BenchmarkService
    
    repository = BenchmarkRepository(db)
    return BenchmarkService(repository)


@lru_cache
def get_settings():
    """Get application settings"""
    from app.config.settings import settings
    return settings