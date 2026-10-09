import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (JSON, Column, DateTime, ForeignKey, Index, Integer,
                        String, Text, desc, select)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.candidates.models import Candidate, CandidateVersion
from app.domain.shared.exceptions import (AdapterConfigError,
                                          CandidateNotFoundError,
                                          CandidateVersionNotFoundError,
                                          InvalidCandidateError,
                                          ValidationError)
from app.logger import get_logger

logger = get_logger(__name__)


class CandidateRepository:
    """Data access layer for candidates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_candidate(self, candidate: Candidate) -> Candidate:
        """Create a new candidate."""
        self.db.add(candidate)
        await self.db.flush()
        return candidate

    async def get_candidate_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Retrieve candidate by ID."""
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def list_candidates(self, skip: int = 0, limit: int = 100) -> List[Candidate]:
        """List all candidates."""
        result = await self.db.execute(
            select(Candidate)
            .order_by(desc(Candidate.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def list_candidates_by_provider(self, provider: str) -> List[Candidate]:
        """List candidates by provider."""
        result = await self.db.execute(
            select(Candidate)
            .where(Candidate.provider == provider)
            .order_by(Candidate.name)
        )
        return result.scalars().all()

    async def create_version(self, version: CandidateVersion) -> CandidateVersion:
        """Create a new candidate version."""
        self.db.add(version)
        await self.db.flush()
        return version

    async def get_version_by_id(self, version_id: str) -> Optional[CandidateVersion]:
        """Retrieve candidate version by ID."""
        result = await self.db.execute(
            select(CandidateVersion).where(CandidateVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_active_version(self, candidate_id: str) -> Optional[CandidateVersion]:
        """Get latest active version of a candidate."""
        result = await self.db.execute(
            select(CandidateVersion)
            .where(CandidateVersion.candidate_id == candidate_id)
            .where(CandidateVersion.status == "active")
            .order_by(desc(CandidateVersion.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_versions(self, candidate_id: str) -> List[CandidateVersion]:
        """List all versions of a candidate."""
        result = await self.db.execute(
            select(CandidateVersion)
            .where(CandidateVersion.candidate_id == candidate_id)
            .order_by(desc(CandidateVersion.created_at))
        )
        return result.scalars().all()
