"""
app/domain/benchmarks/service.py

Copy this file directly to: app/domain/benchmarks/service.py
NO EDITING NEEDED
"""

import hashlib
import json
from typing import Optional, List
from datetime import datetime

from app.domain.benchmarks.models import BenchmarkSuite, BenchmarkVersion
from app.shared.errors import ValidationError, PermissionError, NotFoundError, ConflictError


class BenchmarkService:
    """Business logic for benchmark management"""
    
    def __init__(self, repository):
        self.repository = repository
    
    def create_suite(self, name: str, description: str, owner_id: str) -> BenchmarkSuite:
        """Create new benchmark suite"""
        
        if not name or len(name.strip()) == 0:
            raise ValidationError("Benchmark name is required")
        
        if len(name) > 255:
            raise ValidationError("Benchmark name must be <= 255 characters")
        
        suite = BenchmarkSuite(
            name=name.strip(),
            description=description,
            owner_id=owner_id
        )
        
        return self.repository.create(suite)
    
    def publish_version(self, suite_id: str, version_number: str, tasks: List[dict], owner_id: str) -> BenchmarkVersion:
        """Publish immutable version"""
        
        # Validate ownership
        suite = self.repository.get_suite(suite_id)
        if not suite:
            raise NotFoundError(f"Benchmark suite {suite_id} not found")
        
        if suite.owner_id != owner_id:
            raise PermissionError("Only suite owner can publish versions")
        
        # Validate tasks
        if not tasks or len(tasks) == 0:
            raise ValidationError("At least one task is required")
        
        # Check for duplicate version
        existing = self.repository.get_version_by_number(suite_id, version_number)
        if existing:
            raise ConflictError(f"Version {version_number} already exists for this suite")
        
        # Calculate checksum
        checksum = self._calculate_checksum(tasks)
        
        # Create version
        version = BenchmarkVersion(
            suite_id=suite_id,
            version_number=version_number,
            status="published",
            checksum=checksum,
            task_count=len(tasks),
            published_at=datetime.utcnow()
        )
        
        return self.repository.create_version(version, tasks)
    
    def list_suites(self, owner_id: str, limit: int = 50) -> List[BenchmarkSuite]:
        """List benchmark suites owned by user"""
        return self.repository.list_suites_by_owner(owner_id, limit)
    
    @staticmethod
    def _calculate_checksum(tasks: List[dict]) -> str:
        """Calculate SHA256 checksum of tasks"""
        tasks_json = json.dumps(tasks, sort_keys=True)
        return hashlib.sha256(tasks_json.encode()).hexdigest()