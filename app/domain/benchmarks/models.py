from unittest.mock import Base
from sqlalchemy import Column, String, Integer, JSON, DateTime, Float, UniqueConstraint, Index, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
# from app.database import Base
from datetime import datetime
import uuid

class Benchmark(Base):
    """Benchmark is the root aggregate."""
    __tablename__ = "benchmarks"
    
    id: str = Column(String(50), primary_key=True, default=lambda: f"bench_{uuid.uuid4().hex[:8]}")
    project_id: str = Column(String(50), index=True)
    name: str = Column(String(255), index=True)
    description: str = Column(String(1000))
    created_by: str = Column(String(100))
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_benchmarks_project_created', 'project_id', 'created_at'),
    )

class BenchmarkVersion(Base):
    """Versioned benchmark specification."""
    __tablename__ = "benchmark_versions"
    
    id: str = Column(String(50), primary_key=True)
    benchmark_id: str = Column(String(50), ForeignKey("benchmarks.id"), index=True)
    version: int = Column(Integer)
    task_count: int = Column(Integer)
    checksum: str = Column(String(64))  # SHA256 of tasks
    released_at: datetime = Column(DateTime)
    released_by: str = Column(String(100))
    is_hidden_test_set: bool = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('benchmark_id', 'version', name='uq_benchmark_version'),
        Index('ix_versions_benchmark', 'benchmark_id', 'released_at'),
    )