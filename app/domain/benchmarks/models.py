"""
app/domain/benchmarks/models.py

Copy this file directly to: app/domain/benchmarks/models.py
NO EDITING NEEDED
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


class BenchmarkSuite(Base):
    """Container for benchmark versions"""
    
    __tablename__ = "benchmark_suites"
    __table_args__ = (Index("idx_benchmark_suites_owner", "owner_id"),)
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    versions = relationship("BenchmarkVersion", back_populates="suite", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BenchmarkSuite(name={self.name}, owner={self.owner_id})>"


class BenchmarkVersion(Base):
    """Immutable snapshot of benchmark tasks"""
    
    __tablename__ = "benchmark_versions"
    __table_args__ = (Index("idx_benchmark_versions_suite_status", "suite_id", "status"),)
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    suite_id = Column(PG_UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False)
    version_number = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft, published, archived
    checksum = Column(String(64), nullable=True)
    task_count = Column(Integer, nullable=False, default=0)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    suite = relationship("BenchmarkSuite", back_populates="versions")
    
    def is_published(self) -> bool:
        return self.status == "published"
    
    def __repr__(self):
        return f"<BenchmarkVersion(version={self.version_number}, status={self.status})>"