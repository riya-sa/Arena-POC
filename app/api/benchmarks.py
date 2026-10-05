"""
Benchmark management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.schemas import (
    BenchmarkSuiteCreate,
    BenchmarkSuiteResponse,
    BenchmarkVersionResponse,
    TaskCreate,
    TaskResponse
)
from app.models import BenchmarkSuite, BenchmarkVersion, Task
from app.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/benchmarks", response_model=BenchmarkSuiteResponse, status_code=status.HTTP_201_CREATED)
async def create_benchmark(
    benchmark: BenchmarkSuiteCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new benchmark suite with initial tasks.
    
    - **name**: Benchmark name (required)
    - **description**: Optional description
    - **tasks**: List of tasks to include
    
    Returns the created benchmark with version v1.0 (draft status).
    """
    try:
        logger.info(f"Creating benchmark: {benchmark.name}")
        
        # Create benchmark suite
        suite = BenchmarkSuite(
            id=uuid.uuid4(),
            name=benchmark.name,
            description=benchmark.description
        )
        db.add(suite)
        db.flush()  # Get ID without committing
        
        # Create initial version (v1.0, draft)
        version = BenchmarkVersion(
            id=uuid.uuid4(),
            suite_id=suite.id,
            version_number="v1.0",
            status="draft"
        )
        db.add(version)
        db.flush()
        
        # Add tasks
        for task_input in benchmark.tasks:
            task = Task(
                id=uuid.uuid4(),
                benchmark_version_id=version.id,
                task_id=task_input.task_id,
                problem_statement=task_input.problem_statement,
                category=task_input.category,
                difficulty=task_input.difficulty,
                public_tests=task_input.public_tests or []
            )
            db.add(task)
        
        db.commit()
        db.refresh(suite)
        
        logger.info(f"Benchmark created: {suite.id} with {len(benchmark.tasks)} tasks")
        return suite
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating benchmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create benchmark: {str(e)}"
        )


@router.get("/benchmarks", response_model=List[BenchmarkSuiteResponse])
async def list_benchmarks(db: Session = Depends(get_db)):
    """
    List all benchmark suites with their versions and tasks.
    """
    try:
        benchmarks = db.query(BenchmarkSuite).all()
        logger.info(f"Listed {len(benchmarks)} benchmarks")
        return benchmarks
    except Exception as e:
        logger.error(f"Error listing benchmarks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list benchmarks"
        )


@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkSuiteResponse)
async def get_benchmark(
    benchmark_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific benchmark suite with all versions and tasks.
    """
    try:
        benchmark = db.query(BenchmarkSuite).filter(
            BenchmarkSuite.id == benchmark_id
        ).first()
        
        if not benchmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Benchmark {benchmark_id} not found"
            )
        
        logger.info(f"Retrieved benchmark: {benchmark_id}")
        return benchmark
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving benchmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve benchmark"
        )


@router.post("/benchmarks/{benchmark_id}/versions/{version_id}/publish", response_model=BenchmarkVersionResponse)
async def publish_benchmark_version(
    benchmark_id: str,
    version_id: str,
    db: Session = Depends(get_db)
):
    """
    Publish a benchmark version (make immutable).
    Once published, version cannot be edited.
    """
    try:
        version = db.query(BenchmarkVersion).filter(
            BenchmarkVersion.id == version_id,
            BenchmarkVersion.suite_id == benchmark_id
        ).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Benchmark version not found"
            )
        
        if version.status == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Version is already published"
            )
        
        version.status = "published"
        version.published_at = __import__('datetime').datetime.utcnow()
        
        db.commit()
        db.refresh(version)
        
        logger.info(f"Published benchmark version: {version_id}")
        return version
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error publishing version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish version"
        )


@router.get("/benchmarks/{benchmark_id}/versions", response_model=List[BenchmarkVersionResponse])
async def list_benchmark_versions(
    benchmark_id: str,
    db: Session = Depends(get_db)
):
    """
    List all versions of a benchmark.
    """
    try:
        versions = db.query(BenchmarkVersion).filter(
            BenchmarkVersion.suite_id == benchmark_id
        ).order_by(BenchmarkVersion.created_at.desc()).all()
        
        logger.info(f"Listed {len(versions)} versions for benchmark {benchmark_id}")
        return versions
        
    except Exception as e:
        logger.error(f"Error listing versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list versions"
        )


@router.post("/benchmarks/{benchmark_id}/versions/{version_id}/add-tasks", response_model=BenchmarkVersionResponse)
async def add_tasks_to_version(
    benchmark_id: str,
    version_id: str,
    tasks: List[TaskCreate],
    db: Session = Depends(get_db)
):
    """
    Add tasks to a draft benchmark version.
    Cannot add tasks to published versions.
    """
    try:
        version = db.query(BenchmarkVersion).filter(
            BenchmarkVersion.id == version_id,
            BenchmarkVersion.suite_id == benchmark_id
        ).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Benchmark version not found"
            )
        
        if version.status == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add tasks to published version"
            )
        
        for task_input in tasks:
            task = Task(
                id=uuid.uuid4(),
                benchmark_version_id=version.id,
                task_id=task_input.task_id,
                problem_statement=task_input.problem_statement,
                category=task_input.category,
                difficulty=task_input.difficulty,
                public_tests=task_input.public_tests or []
            )
            db.add(task)
        
        db.commit()
        db.refresh(version)
        
        logger.info(f"Added {len(tasks)} tasks to version {version_id}")
        return version
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add tasks"
        )