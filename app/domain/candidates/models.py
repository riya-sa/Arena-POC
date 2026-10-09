"""
Candidates domain models, repository and service.
Files: 
  - app/domain/candidates/models.py
  - app/domain/candidates/repository.py
  - app/domain/candidates/service.py
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional
import uuid

from app.database import Base
from app.domain.shared.exceptions import (
    CandidateNotFoundError,
    CandidateVersionNotFoundError,
    InvalidCandidateError,
    ValidationError,
    AdapterConfigError
)
from app.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Models
# ============================================================================

class Candidate(Base):
    """
    Model candidate aggregate root.
    Represents a single model/agent that can be evaluated.
    """
    __tablename__ = "candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)  # e.g., "Claude 3.5 Sonnet"
    provider = Column(String(100), nullable=False)  # anthropic, openai, local, mock
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = relationship(
        "CandidateVersion",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    __table_args__ = (
        Index("ix_candidates_provider", "provider"),
    )
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name={self.name}, provider={self.provider})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "provider": self.provider,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class CandidateVersion(Base):
    """
    Model configuration version.
    Represents a specific model + configuration combination.
    """
    __tablename__ = "candidate_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)  # 1.0, 1.1, 2.0
    model_id = Column(String(255), nullable=False)  # e.g., "claude-3-5-sonnet-20241022"
    config = Column(JSON, nullable=False)  # {temperature, max_tokens, pricing, etc.}
    status = Column(String(50), nullable=False, default="active")  # active, deprecated
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="versions", lazy="select")
    
    __table_args__ = (
        Index("ix_candidate_versions_candidate", "candidate_id"),
        Index("ix_candidate_versions_status", "status"),
    )
    
    def __repr__(self):
        return f"<CandidateVersion(id={self.id}, version={self.version_number})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            "version_number": self.version_number,
            "model_id": self.model_id,
            "config": self.config,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


# ============================================================================
# Repository Layer
# ============================================================================




