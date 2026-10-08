"""
app/domain/benchmarks/repository.py

Copy this file directly to: app/domain/benchmarks/repository.py
NO EDITING NEEDED
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.benchmarks.models import BenchmarkSuite, BenchmarkVersion


class BenchmarkRepository:
    """Data access layer for benchmarks"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, suite: BenchmarkSuite) -> BenchmarkSuite:
        """Create new suite"""
        self.session.add(suite)
        self.session.commit()
        self.session.refresh(suite)
        return suite
    
    def create_version(self, version: BenchmarkVersion, tasks: List[dict]) -> BenchmarkVersion:
        """Create new version with tasks"""
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return version
    
    def get_suite(self, suite_id: str) -> Optional[BenchmarkSuite]:
        """Get suite by ID"""
        try:
            suite_uuid = UUID(suite_id)
            return self.session.query(BenchmarkSuite).filter(
                BenchmarkSuite.id == suite_uuid
            ).first()
        except (ValueError, TypeError):
            return None
    
    def get_version_by_number(self, suite_id: str, version_number: str) -> Optional[BenchmarkVersion]:
        """Get specific version"""
        try:
            suite_uuid = UUID(suite_id)
            return self.session.query(BenchmarkVersion).filter(
                BenchmarkVersion.suite_id == suite_uuid,
                BenchmarkVersion.version_number == version_number
            ).first()
        except (ValueError, TypeError):
            return None
    
    def list_suites_by_owner(self, owner_id: str, limit: int = 50) -> List[BenchmarkSuite]:
        """List suites owned by user"""
        return self.session.query(BenchmarkSuite).filter(
            BenchmarkSuite.owner_id == owner_id
        ).order_by(
            BenchmarkSuite.created_at.desc()
        ).limit(limit).all()