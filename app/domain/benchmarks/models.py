"""
Benchmark domain models.
File: app/domain/benchmarks/models.py
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class BenchmarkSuite(Base):
    """
    Benchmark suite aggregate root.
    Represents a collection of benchmark tasks.
    """
    __tablename__ = "benchmark_suites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = relationship(
        "BenchmarkVersion",
        back_populates="suite",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<BenchmarkSuite(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class BenchmarkVersion(Base):
    """
    Immutable benchmark version.
    Each version represents a snapshot of tasks at a point in time.
    Once published, cannot be modified.
    """
    __tablename__ = "benchmark_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)  # v1.0, v1.1, v2.0
    status = Column(String(50), nullable=False, default="draft")  # draft, published
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Metadata
    task_count = Column(Integer, nullable=False, default=0)
    checksum = Column(String(64), nullable=True)  # SHA256 of tasks for integrity
    
    # Relationships
    suite = relationship("BenchmarkSuite", back_populates="versions", lazy="select")
    tasks = relationship(
        "Task",
        back_populates="benchmark_version",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    __table_args__ = (
        Index("ix_versions_suite_status", "suite_id", "status"),
        Index("ix_versions_suite_version", "suite_id", "version_number"),
    )
    
    def __repr__(self):
        return f"<BenchmarkVersion(id={self.id}, version={self.version_number}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "suite_id": str(self.suite_id),
            "version_number": self.version_number,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat(),
            "task_count": self.task_count
        }
    
    @property
    def is_published(self) -> bool:
        """Check if version is immutable (published)."""
        return self.status == "published"


class Task(Base):
    """
    Individual benchmark task within a version.
    Cannot be modified after parent version is published.
    """
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benchmark_version_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_versions.id"), nullable=False, index=True)
    
    # Task identification
    task_id = Column(String(100), nullable=False)  # java-001, java-002, etc.
    problem_statement = Column(Text, nullable=False)  # Full problem description
    
    # Metadata
    category = Column(String(100), nullable=True)  # recursion, dp, sorting, etc.
    difficulty = Column(Integer, nullable=True)  # 1-5 stars
    
    # Test cases
    public_tests = Column(JSON, nullable=False)  # List of test cases (visible to models)
    # hidden_tests encrypted/stored separately for security
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    benchmark_version = relationship("BenchmarkVersion", back_populates="tasks", lazy="select")
    
    __table_args__ = (
        Index("ix_tasks_benchmark_version", "benchmark_version_id"),
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, task_id={self.task_id})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "benchmark_version_id": str(self.benchmark_version_id),
            "task_id": self.task_id,
            "problem_statement": self.problem_statement,
            "category": self.category,
            "difficulty": self.difficulty,
            "public_tests": self.public_tests,
            "created_at": self.created_at.isoformat()
        }