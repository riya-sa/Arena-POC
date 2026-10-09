from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional
import uuid

from app.database import Base
from app.domain.candidates.models import Candidate, CandidateVersion
from app.domain.candidates.repository import CandidateRepository
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
# Service Layer
# ============================================================================

class CandidateService:
    """Candidate business logic."""
    
    def __init__(self, repo: CandidateRepository):
        self.repo = repo
    
    async def register_candidate(
        self,
        name: str,
        provider: str,
        model_id: str,
        description: str = None,
        config: dict = None
    ) -> Candidate:
        """
        Register a new model candidate.
        
        Args:
            name: Display name (e.g., "GPT-4")
            provider: Provider name (anthropic, openai, local, mock)
            model_id: Model identifier (e.g., "gpt-4")
            description: Optional description
            config: Model configuration (temperature, max_tokens, pricing, etc.)
            
        Returns:
            Created Candidate with initial v1.0 version
            
        Raises:
            ValidationError: If inputs invalid
            AdapterConfigError: If provider not supported
        """
        # Validate
        if not name or len(name) < 2:
            raise ValidationError("Candidate name must be at least 2 characters")
        
        if provider.lower() not in ["anthropic", "openai", "local", "mock"]:
            raise AdapterConfigError(f"Unknown provider: {provider}")
        
        if not model_id or len(model_id) < 1:
            raise ValidationError("model_id is required")
        
        # Create candidate
        candidate = Candidate(
            name=name,
            provider=provider.lower(),
            description=description
        )
        await self.repo.create_candidate(candidate)
        
        # Create initial version (v1.0, active)
        version = CandidateVersion(
            candidate_id=candidate.id,
            version_number="1.0",
            model_id=model_id,
            config=self._build_config(provider, config or {}),
            status="active"
        )
        await self.repo.create_version(version)
        
        logger.info(f"Registered candidate: {candidate.id} ({name}, {provider})")
        return candidate
    
    async def get_candidate(self, candidate_id: str) -> Candidate:
        """
        Retrieve candidate.
        
        Raises:
            CandidateNotFoundError: If not found
        """
        candidate = await self.repo.get_candidate_by_id(candidate_id)
        if not candidate:
            raise CandidateNotFoundError(f"Candidate not found: {candidate_id}")
        return candidate
    
    async def get_active_version(self, candidate_id: str) -> CandidateVersion:
        """
        Get active version of candidate.
        
        Raises:
            CandidateNotFoundError: If candidate not found
            CandidateVersionNotFoundError: If no active version
        """
        candidate = await self.get_candidate(candidate_id)
        
        version = await self.repo.get_active_version(candidate_id)
        if not version:
            raise CandidateVersionNotFoundError(
                f"No active version for candidate: {candidate_id}"
            )
        
        return version
    
    async def get_version(self, version_id: str) -> CandidateVersion:
        """
        Retrieve specific candidate version.
        
        Raises:
            CandidateVersionNotFoundError: If not found
        """
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise CandidateVersionNotFoundError(f"Version not found: {version_id}")
        return version
    
    async def create_version(
        self,
        candidate_id: str,
        version_number: str,
        model_id: str,
        config: dict = None
    ) -> CandidateVersion:
        """
        Create a new version of a candidate.
        
        Args:
            candidate_id: Parent candidate
            version_number: New version (e.g., "2.0")
            model_id: Model identifier
            config: Configuration overrides
            
        Returns:
            New CandidateVersion (active)
            
        Raises:
            CandidateNotFoundError: If candidate not found
            ValidationError: If version already exists
        """
        candidate = await self.get_candidate(candidate_id)
        
        # Check version doesn't exist
        existing_versions = await self.repo.list_versions(candidate_id)
        if any(v.version_number == version_number for v in existing_versions):
            raise ValidationError(f"Version {version_number} already exists")
        
        version = CandidateVersion(
            candidate_id=candidate_id,
            version_number=version_number,
            model_id=model_id,
            config=self._build_config(candidate.provider, config or {}),
            status="active"
        )
        await self.repo.create_version(version)
        
        logger.info(f"Created version {version_number} for candidate {candidate_id}")
        return version
    
    async def deprecate_version(self, version_id: str) -> CandidateVersion:
        """
        Mark a version as deprecated (no longer used).
        
        Raises:
            CandidateVersionNotFoundError: If not found
        """
        version = await self.get_version(version_id)
        version.status = "deprecated"
        
        logger.info(f"Deprecated version {version_id}")
        return version
    
    # Private helper methods
    
    def _build_config(self, provider: str, user_config: dict) -> dict:
        """
        Build complete config with provider defaults.
        Merges user config over provider defaults.
        """
        # Provider defaults
        defaults = {
            "anthropic": {
                "input_price_per_1k_tokens": 0.003,
                "output_price_per_1k_tokens": 0.015,
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "openai": {
                "input_price_per_1k_tokens": 0.01,
                "output_price_per_1k_tokens": 0.03,
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "local": {
                "input_price_per_1k_tokens": 0.0,
                "output_price_per_1k_tokens": 0.0,
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "mock": {
                "input_price_per_1k_tokens": 0.0,
                "output_price_per_1k_tokens": 0.0,
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
        
        provider_defaults = defaults.get(provider.lower(), defaults["mock"])
        return {**provider_defaults, **user_config}