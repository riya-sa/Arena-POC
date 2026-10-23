
"""Job submission and management endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.domain.jobs import (
    JobSubmitRequest,
    JobResponse,
    JobDetailResponse,
    JobService
)
from app.logger import logger


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Not found"}}
)


@router.post("/submit", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(request: JobSubmitRequest) -> JobResponse:
    """Submit a job for distributed execution."""
    try:
        job = JobService.submit_job(
            experiment_id=request.experiment_id,
            candidate_id=request.candidate_id,
            candidate_name=request.candidate_name,
            tasks=request.tasks
        )
        
        return JobResponse(
            id=job.id,
            experiment_id=job.experiment_id,
            candidate_id=job.candidate_id,
            status=job.status,
            progress_percent=job.progress_percent(),
            total_tasks=job.total_tasks,
            completed_tasks=job.completed_tasks,
            failed_tasks=job.failed_tasks,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
    except Exception as e:
        logger.error(f"Failed to submit job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str) -> JobResponse:
    """Get job status and progress."""
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return JobResponse(
        id=job.id,
        experiment_id=job.experiment_id,
        candidate_id=job.candidate_id,
        status=job.status,
        progress_percent=job.progress_percent(),
        total_tasks=job.total_tasks,
        completed_tasks=job.completed_tasks,
        failed_tasks=job.failed_tasks,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get("/{job_id}/detail", response_model=JobDetailResponse)
async def get_job_detail(job_id: str) -> JobDetailResponse:
    """Get detailed job information including results."""
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return JobDetailResponse(
        id=job.id,
        experiment_id=job.experiment_id,
        candidate_id=job.candidate_id,
        status=job.status,
        progress_percent=job.progress_percent(),
        total_tasks=job.total_tasks,
        completed_tasks=job.completed_tasks,
        failed_tasks=job.failed_tasks,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        tasks=job.tasks,
        results=job.results,
        error_message=job.error_message
    )


@router.get("/queue/stats")
async def get_queue_stats():
    """Get job queue statistics."""
    from app.infrastructure.queue import get_queue
    
    try:
        queue = get_queue()
        return {
            "queue_length": queue.get_queue_length(),
            "active_jobs": queue.get_active_jobs(),
            "active_count": len(queue.get_active_jobs())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue unavailable: {str(e)}"
        )