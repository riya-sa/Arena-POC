from typing import Optional
from sqlalchemy.orm import Session
from app.domain.benchmarks.models import BenchmarkSuite, BenchmarkVersion

class BenchmarkRepository:
    """Data access for benchmarks"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, suite: BenchmarkSuite) -> BenchmarkSuite:
        self.session.add(suite)
        self.session.commit()
        return suite
    
    def get_suite(self, suite_id: str) -> Optional[BenchmarkSuite]:
        return self.session.query(BenchmarkSuite).filter(
            BenchmarkSuite.id == suite_id
        ).first()
    
    def create_version(self, version: BenchmarkVersion, tasks: list) -> BenchmarkVersion:
        self.session.add(version)
        # Add tasks...
        self.session.commit()
        return version