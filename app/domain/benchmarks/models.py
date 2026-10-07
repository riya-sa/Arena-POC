from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base

class BenchmarkSuite(Base):
    """Container for benchmark versions"""
    __tablename__ = "benchmark_suites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String(255), nullable=False)  # RBAC owner
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    versions = relationship("BenchmarkVersion", back_populates="suite", cascade="all, delete-orphan")

class BenchmarkVersion(Base):
    """Immutable snapshot of benchmark"""
    __tablename__ = "benchmark_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False)
    version_number = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, published, archived
    checksum = Column(String(64), nullable=True)  # SHA256 of tasks
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    suite = relationship("BenchmarkSuite", back_populates="versions")
    tasks = relationship("Task", back_populates="benchmark_version", cascade="all, delete-orphan")
    
    def is_published(self) -> bool:
        return self.status == "published"
    
    def is_immutable(self) -> bool:
        return self.is_published()