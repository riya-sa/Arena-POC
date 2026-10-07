from typing import Optional
from app.domain.benchmarks.models import BenchmarkSuite, BenchmarkVersion
from app.domain.benchmarks.repository import BenchmarkRepository
from app.shared.errors import ValidationError, PermissionError
from sqlalchemy.orm import Session
import hashlib
import json

class BenchmarkService:
    """Business logic for benchmarks"""
    
    def __init__(self, repository: BenchmarkRepository):
        self.repository = repository
    
    def create_suite(self, name: str, description: str, owner_id: str) -> BenchmarkSuite:
        """Create new benchmark suite"""
        suite = BenchmarkSuite(
            name=name,
            description=description,
            owner_id=owner_id
        )
        return self.repository.create(suite)
    
    def publish_version(
        self, 
        suite_id: str, 
        version_number: str, 
        tasks: list,
        owner_id: str
    ) -> BenchmarkVersion:
        """Publish immutable version"""
        
        # Validate owner
        suite = self.repository.get_suite(suite_id)
        if suite.owner_id != owner_id:
            raise PermissionError("Only suite owner can publish versions")
        
        # Calculate checksum for integrity
        checksum = self._calculate_checksum(tasks)
        
        # Create version
        version = BenchmarkVersion(
            suite_id=suite_id,
            version_number=version_number,
            status="published",
            checksum=checksum,
            published_at=datetime.utcnow()
        )
        
        return self.repository.create_version(version, tasks)
    
    def _calculate_checksum(self, tasks: list) -> str:
        """Calculate SHA256 of tasks for integrity"""
        tasks_json = json.dumps(tasks, sort_keys=True)
        return hashlib.sha256(tasks_json.encode()).hexdigest()