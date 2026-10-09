"""
Benchmark domain repository and service.
File: app/domain/benchmarks/repository.py + service.py
"""

import hashlib
import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.benchmarks.models import BenchmarkSuite, BenchmarkVersion, Task
from app.domain.shared.exceptions import (BenchmarkAlreadyPublishedError,
                                          BenchmarkNotFoundError,
                                          BenchmarkVersionNotFoundError,
                                          InvalidTaskError, TaskNotFoundError,
                                          ValidationError)
from app.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Repository Layer - Data Access
# ============================================================================


class BenchmarkRepository:
    """
    Data access layer for benchmark aggregates.
    Abstracts database operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_suite(self, suite: BenchmarkSuite) -> BenchmarkSuite:
        """Create a new benchmark suite."""
        self.db.add(suite)
        await self.db.flush()
        return suite

    async def get_suite_by_id(self, suite_id: str) -> Optional[BenchmarkSuite]:
        """Retrieve benchmark suite by ID with versions and tasks."""
        result = await self.db.execute(
            select(BenchmarkSuite).where(BenchmarkSuite.id == suite_id)
        )
        return result.scalar_one_or_none()

    async def list_suites(
        self, skip: int = 0, limit: int = 100
    ) -> List[BenchmarkSuite]:
        """List all benchmark suites."""
        result = await self.db.execute(
            select(BenchmarkSuite)
            .order_by(desc(BenchmarkSuite.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_version(self, version: BenchmarkVersion) -> BenchmarkVersion:
        """Create a new benchmark version."""
        self.db.add(version)
        await self.db.flush()
        return version

    async def get_version_by_id(self, version_id: str) -> Optional[BenchmarkVersion]:
        """Retrieve specific benchmark version."""
        result = await self.db.execute(
            select(BenchmarkVersion).where(BenchmarkVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_version_by_number(
        self, suite_id: str, version_number: str
    ) -> Optional[BenchmarkVersion]:
        """Retrieve benchmark version by suite and version number."""
        result = await self.db.execute(
            select(BenchmarkVersion)
            .where(BenchmarkVersion.suite_id == suite_id)
            .where(BenchmarkVersion.version_number == version_number)
        )
        return result.scalar_one_or_none()

    async def list_versions(self, suite_id: str) -> List[BenchmarkVersion]:
        """List all versions of a benchmark suite."""
        result = await self.db.execute(
            select(BenchmarkVersion)
            .where(BenchmarkVersion.suite_id == suite_id)
            .order_by(desc(BenchmarkVersion.created_at))
        )
        return result.scalars().all()

    async def get_tasks_by_version(self, version_id: str) -> List[Task]:
        """Retrieve all tasks in a benchmark version."""
        result = await self.db.execute(
            select(Task)
            .where(Task.benchmark_version_id == version_id)
            .order_by(Task.task_id)
        )
        return result.scalars().all()

    async def create_task(self, task: Task) -> Task:
        """Create a new task in a benchmark version."""
        self.db.add(task)
        await self.db.flush()
        return task

    async def create_tasks_bulk(self, tasks: List[Task]) -> List[Task]:
        """Create multiple tasks at once."""
        for task in tasks:
            self.db.add(task)
        await self.db.flush()
        return tasks

    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Retrieve task by ID."""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()


# ============================================================================
# Service Layer - Business Logic
# ============================================================================


class BenchmarkService:
    """
    Benchmark business logic.
    Enforces domain rules and invariants.
    """

    def __init__(self, repo: BenchmarkRepository):
        self.repo = repo

    async def create_benchmark_suite(
        self, name: str, description: str = None
    ) -> BenchmarkSuite:
        """
        Create a new benchmark suite.
        Automatically creates v1.0 in draft status.

        Args:
            name: Benchmark name (required, min 3 chars)
            description: Optional description

        Returns:
            BenchmarkSuite with initial draft version

        Raises:
            ValidationError: If name invalid
        """
        # Validate
        if not name or len(name) < 3:
            raise ValidationError("Benchmark name must be at least 3 characters")

        # Create suite
        suite = BenchmarkSuite(name=name, description=description)
        await self.repo.create_suite(suite)

        # Create initial version (v1.0, draft)
        version = BenchmarkVersion(
            suite_id=suite.id, version_number="v1.0", status="draft", task_count=0
        )
        await self.repo.create_version(version)

        logger.info(f"Created benchmark suite: {suite.id} ({name})")
        return suite

    async def get_suite(self, suite_id: str) -> BenchmarkSuite:
        """
        Retrieve benchmark suite.

        Raises:
            BenchmarkNotFoundError: If suite doesn't exist
        """
        suite = await self.repo.get_suite_by_id(suite_id)
        if not suite:
            raise BenchmarkNotFoundError(f"Benchmark suite not found: {suite_id}")
        return suite

    async def get_version(self, version_id: str) -> BenchmarkVersion:
        """
        Retrieve benchmark version.

        Raises:
            BenchmarkVersionNotFoundError: If version doesn't exist
        """
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise BenchmarkVersionNotFoundError(
                f"Benchmark version not found: {version_id}"
            )
        return version

    async def add_tasks(self, version_id: str, tasks_data: List[dict]) -> List[Task]:
        """
        Add tasks to a benchmark version.
        Can only add to draft versions.

        Args:
            version_id: Target benchmark version
            tasks_data: List of task definitions

        Returns:
            Created Task objects

        Raises:
            BenchmarkAlreadyPublishedError: If version is published
            InvalidTaskError: If task data invalid
        """
        # Verify version exists and is not published
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise BenchmarkVersionNotFoundError(
                f"Benchmark version not found: {version_id}"
            )

        if version.is_published:
            raise BenchmarkAlreadyPublishedError(
                f"Cannot add tasks to published version: {version_id}"
            )

        # Validate and create tasks
        created_tasks = []
        for task_data in tasks_data:
            # Validate task
            self._validate_task_data(task_data)

            task = Task(
                benchmark_version_id=version_id,
                task_id=task_data["task_id"],
                problem_statement=task_data["problem_statement"],
                category=task_data.get("category"),
                difficulty=task_data.get("difficulty"),
                public_tests=task_data.get("public_tests", []),
            )

            await self.repo.create_task(task)
            created_tasks.append(task)

        # Update version metadata
        version.task_count = len(await self.repo.get_tasks_by_version(version_id))

        logger.info(f"Added {len(created_tasks)} tasks to version {version_id}")
        return created_tasks

    async def publish_version(self, version_id: str) -> BenchmarkVersion:
        """
        Publish a benchmark version (make immutable).

        Args:
            version_id: Version to publish

        Returns:
            Published BenchmarkVersion

        Raises:
            BenchmarkVersionNotFoundError: If version doesn't exist
            BenchmarkAlreadyPublishedError: If already published
            ValidationError: If version has no tasks
        """
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise BenchmarkVersionNotFoundError(
                f"Benchmark version not found: {version_id}"
            )

        if version.is_published:
            raise BenchmarkAlreadyPublishedError(
                f"Benchmark version already published: {version_id}"
            )

        # Must have at least one task
        tasks = await self.repo.get_tasks_by_version(version_id)
        if not tasks:
            raise ValidationError("Cannot publish version with no tasks")

        # Update status
        version.status = "published"
        version.published_at = datetime.utcnow()
        version.task_count = len(tasks)

        # Compute checksum for integrity
        version.checksum = self._compute_tasks_checksum(tasks)

        logger.info(
            f"Published benchmark version: {version_id} with {len(tasks)} tasks"
        )
        return version

    async def create_new_version(
        self, suite_id: str, version_number: str
    ) -> BenchmarkVersion:
        """
        Create a new version of a benchmark suite.
        New version starts as draft (can be edited).

        Args:
            suite_id: Benchmark suite
            version_number: New version (e.g., "v2.0")

        Returns:
            New BenchmarkVersion in draft status

        Raises:
            BenchmarkNotFoundError: If suite doesn't exist
            ValidationError: If version number already exists
        """
        # Verify suite exists
        suite = await self.repo.get_suite_by_id(suite_id)
        if not suite:
            raise BenchmarkNotFoundError(f"Benchmark suite not found: {suite_id}")

        # Check version doesn't already exist
        existing = await self.repo.get_version_by_number(suite_id, version_number)
        if existing:
            raise ValidationError(f"Version {version_number} already exists")

        # Create new version
        version = BenchmarkVersion(
            suite_id=suite_id,
            version_number=version_number,
            status="draft",
            task_count=0,
        )
        await self.repo.create_version(version)

        logger.info(f"Created new version {version_number} for suite {suite_id}")
        return version

    # Private validation methods

    def _validate_task_data(self, task_data: dict) -> None:
        """Validate task definition."""
        if not task_data.get("task_id"):
            raise InvalidTaskError("task_id is required")

        if not task_data.get("problem_statement"):
            raise InvalidTaskError("problem_statement is required")

        if task_data.get("difficulty") is not None:
            difficulty = task_data["difficulty"]
            if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
                raise InvalidTaskError("difficulty must be 1-5")

    def _compute_tasks_checksum(self, tasks: List[Task]) -> str:
        """
        Compute SHA256 checksum of all tasks for integrity verification.
        """
        task_data = [
            {
                "task_id": t.task_id,
                "problem": t.problem_statement[:100],  # First 100 chars
                "tests": len(t.public_tests),
            }
            for t in sorted(tasks, key=lambda t: t.task_id)
        ]

        data_str = json.dumps(task_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
