# """
# SQLAlchemy models for C/AI Arena POC
# """

# from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, DECIMAL, JSON
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# from datetime import datetime
# import uuid

# from app.database import Base


# class BenchmarkSuite(Base):
#     """Benchmark task collection."""
#     __tablename__ = "benchmark_suites"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String(255), nullable=False, index=True)
#     description = Column(Text, nullable=True)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     versions = relationship("BenchmarkVersion", back_populates="suite", cascade="all, delete-orphan")
    
#     def __repr__(self):
#         return f"<BenchmarkSuite(id={self.id}, name={self.name})>"


# class BenchmarkVersion(Base):
#     """Immutable benchmark version."""
#     __tablename__ = "benchmark_versions"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     suite_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False, index=True)
#     version_number = Column(String(20), nullable=False)  # v1.0, v1.1
#     status = Column(String(50), nullable=False, default="draft")  # draft, published
#     published_at = Column(DateTime, nullable=True)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     suite = relationship("BenchmarkSuite", back_populates="versions")
#     tasks = relationship("Task", back_populates="benchmark_version", cascade="all, delete-orphan")
    
#     __table_args__ = (
#         # Ensure unique version per suite
#     )
    
#     def __repr__(self):
#         return f"<BenchmarkVersion(id={self.id}, version={self.version_number}, status={self.status})>"


# class Task(Base):
#     """Individual benchmark task."""
#     __tablename__ = "tasks"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     benchmark_version_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_versions.id"), nullable=False, index=True)
#     task_id = Column(String(100), nullable=False)  # java-001, java-002
#     problem_statement = Column(Text, nullable=False)
#     category = Column(String(100), nullable=True)  # recursion, dp, sorting
#     difficulty = Column(Integer, nullable=True)  # 1-5 stars
#     public_tests = Column(JSON, nullable=False)  # { "test_1": {...}, ... }
#     hidden_tests_encrypted = Column(Text, nullable=True)  # Encrypted (for MVP)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     benchmark_version = relationship("BenchmarkVersion", back_populates="tasks")
    
#     def __repr__(self):
#         return f"<Task(id={self.id}, task_id={self.task_id})>"


# class Candidate(Base):
#     """AI model candidate."""
#     __tablename__ = "candidates"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String(255), nullable=False, index=True)  # Claude-3.5-Sonnet
#     provider = Column(String(100), nullable=False)  # anthropic, openai, local
#     description = Column(Text, nullable=True)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     versions = relationship("CandidateVersion", back_populates="candidate", cascade="all, delete-orphan")
    
#     def __repr__(self):
#         return f"<Candidate(id={self.id}, name={self.name})>"


# class CandidateVersion(Base):
#     """Model configuration version."""
#     __tablename__ = "candidate_versions"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
#     version_number = Column(String(20), nullable=False)  # 1.0, 1.1
#     model_id = Column(String(255), nullable=False)  # claude-3-5-sonnet-20241022
#     config = Column(JSON, nullable=False)  # { "temperature": 0.7, "max_tokens": 2048 }
#     status = Column(String(50), nullable=False, default="active")  # active, deprecated
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     candidate = relationship("Candidate", back_populates="versions")
    
#     def __repr__(self):
#         return f"<CandidateVersion(id={self.id}, version={self.version_number})>"


# class Experiment(Base):
#     """Benchmark experiment run."""
#     __tablename__ = "experiments"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     benchmark_version_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_versions.id"), nullable=False, index=True)
#     name = Column(String(255), nullable=True)
#     status = Column(String(50), nullable=False, default="created")  # created, queued, running, complete, failed
#     repetitions = Column(Integer, nullable=False, default=1)
#     budget_usd = Column(DECIMAL(10, 2), nullable=True)
#     spent_usd = Column(DECIMAL(10, 2), nullable=False, default=0)
#     submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
#     started_at = Column(DateTime, nullable=True)
#     completed_at = Column(DateTime, nullable=True)
#     error_message = Column(Text, nullable=True)
    
#     # Relationships
#     benchmark_version = relationship("BenchmarkVersion")
#     executions = relationship("Execution", back_populates="experiment", cascade="all, delete-orphan")
    
#     def __repr__(self):
#         return f"<Experiment(id={self.id}, status={self.status})>"


# class Execution(Base):
#     """Individual task-candidate execution."""
#     __tablename__ = "executions"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False, index=True)
#     task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
#     candidate_version_id = Column(UUID(as_uuid=True), ForeignKey("candidate_versions.id"), nullable=False, index=True)
#     repetition_number = Column(Integer, nullable=False)  # 1, 2, 3
#     status = Column(String(50), nullable=False, default="queued")  # queued, running, complete, failed
#     enqueued_at = Column(DateTime, nullable=True)
#     started_at = Column(DateTime, nullable=True)
#     completed_at = Column(DateTime, nullable=True)
#     error_message = Column(Text, nullable=True)
    
#     # Telemetry
#     latency_ms = Column(Integer, nullable=True)
#     input_tokens = Column(Integer, nullable=True)
#     output_tokens = Column(Integer, nullable=True)
#     cost_usd = Column(DECIMAL(10, 4), nullable=True)
#     model_response = Column(Text, nullable=True)  # Full response
    
#     # Evaluation
#     passed = Column(Boolean, nullable=True)
#     score = Column(Integer, nullable=True)  # 0-100
#     evaluation_details = Column(JSON, nullable=True)
    
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     experiment = relationship("Experiment", back_populates="executions")
#     task = relationship("Task")
#     candidate_version = relationship("CandidateVersion")
    
#     def __repr__(self):
#         return f"<Execution(id={self.id}, status={self.status})>"

"""
SQLAlchemy models for C/AI Arena POC
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class BenchmarkSuite(Base):
    """Benchmark task collection."""
    __tablename__ = "benchmark_suites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    versions = relationship("BenchmarkVersion", back_populates="suite", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BenchmarkSuite(id={self.id}, name={self.name})>"


class BenchmarkVersion(Base):
    """Immutable benchmark version."""
    __tablename__ = "benchmark_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)  # v1.0, v1.1
    status = Column(String(50), nullable=False, default="draft")  # draft, published
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    suite = relationship("BenchmarkSuite", back_populates="versions")
    tasks = relationship("Task", back_populates="benchmark_version", cascade="all, delete-orphan")
    
    __table_args__ = (
        # Ensure unique version per suite
    )
    
    def __repr__(self):
        return f"<BenchmarkVersion(id={self.id}, version={self.version_number}, status={self.status})>"


class Task(Base):
    """Individual benchmark task."""
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benchmark_version_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_versions.id"), nullable=False, index=True)
    task_id = Column(String(100), nullable=False)  # java-001, java-002
    problem_statement = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # recursion, dp, sorting
    difficulty = Column(Integer, nullable=True)  # 1-5 stars
    public_tests = Column(JSON, nullable=False)  # { "test_1": {...}, ... }
    hidden_tests_encrypted = Column(Text, nullable=True)  # Encrypted (for MVP)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    benchmark_version = relationship("BenchmarkVersion", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, task_id={self.task_id})>"


class Candidate(Base):
    """AI model candidate."""
    __tablename__ = "candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)  # Claude-3.5-Sonnet
    provider = Column(String(100), nullable=False)  # anthropic, openai, local
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    versions = relationship("CandidateVersion", back_populates="candidate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name={self.name})>"


class CandidateVersion(Base):
    """Model configuration version."""
    __tablename__ = "candidate_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)  # 1.0, 1.1
    model_id = Column(String(255), nullable=False)  # claude-3-5-sonnet-20241022
    config = Column(JSON, nullable=False)  # { "temperature": 0.7, "max_tokens": 2048 }
    status = Column(String(50), nullable=False, default="active")  # active, deprecated
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="versions")
    
    def __repr__(self):
        return f"<CandidateVersion(id={self.id}, version={self.version_number})>"


class Experiment(Base):
    """Benchmark experiment run."""
    __tablename__ = "experiments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benchmark_version_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_versions.id"), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="created")  # created, queued, running, complete, failed
    repetitions = Column(Integer, nullable=False, default=1)
    budget_usd = Column(DECIMAL(10, 2), nullable=True)
    spent_usd = Column(DECIMAL(10, 2), nullable=False, default=0)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    benchmark_version = relationship("BenchmarkVersion")
    executions = relationship("Execution", back_populates="experiment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Experiment(id={self.id}, status={self.status})>"


class Execution(Base):
    """Individual task-candidate execution."""
    __tablename__ = "executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    candidate_version_id = Column(UUID(as_uuid=True), ForeignKey("candidate_versions.id"), nullable=False, index=True)
    repetition_number = Column(Integer, nullable=False)  # 1, 2, 3
    status = Column(String(50), nullable=False, default="queued")  # queued, running, complete, failed
    enqueued_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Telemetry
    latency_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost_usd = Column(DECIMAL(10, 4), nullable=True)
    model_response = Column(Text, nullable=True)  # Full response
    
    # Evaluation
    passed = Column(Boolean, nullable=True)
    score = Column(Integer, nullable=True)  # 0-100
    evaluation_details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    experiment = relationship("Experiment", back_populates="executions")
    task = relationship("Task")
    candidate_version = relationship("CandidateVersion")
    
    def __repr__(self):
        return f"<Execution(id={self.id}, status={self.status})>"