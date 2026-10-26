
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

@router.get("/{job_id}/progress")
async def get_job_progress(job_id: str):
    """Get real-time job progress."""
    from app.domain.jobs import JobService
    
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job.status.value,
        "progress": job.progress_percent(),
        "completed": job.completed_tasks,
        "total": job.total_tasks,
        "failed": job.failed_tasks,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

@router.get("/experiment/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """Get aggregated results for an experiment."""
    from app.infrastructure.queue import get_queue
    from app.domain.jobs.aggregator import ResultAggregator
    
    # Get all jobs for this experiment
    queue = get_queue()
    all_keys = queue.redis_client.keys(f"{queue.job_prefix}*")
    
    experiment_jobs = []
    for key in all_keys:
        try:
            job_json = queue.redis_client.get(key)
            if job_json:
                from app.domain.jobs import Job
                job = Job.from_json(job_json)
                if job.experiment_id == experiment_id:
                    experiment_jobs.append(job.id)
        except:
            continue
    
    if not experiment_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No jobs found for experiment {experiment_id}"
        )
    
    results = ResultAggregator.aggregate_experiment_results(
        experiment_id,
        experiment_jobs
    )
    
    return results

@router.get("/system/metrics")
async def get_system_metrics():
    """Get system and execution metrics."""
    from app.infrastructure.metrics import get_metrics
    from app.infrastructure.queue import get_queue
    from app.workers import get_worker_manager
    
    metrics = get_metrics().get_metrics()
    
    try:
        queue = get_queue()
        metrics["queue"] = {
            "pending_jobs": queue.get_queue_length(),
            "active_jobs": len(queue.get_active_jobs())
        }
    except:
        metrics["queue"] = {"pending_jobs": 0, "active_jobs": 0}
    
    worker_mgr = get_worker_manager()
    if worker_mgr:
        metrics["workers"] = worker_mgr.get_stats()
    
    return metrics