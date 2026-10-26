"""Job execution service."""

from typing import List, Optional
from datetime import datetime
from app.domain.jobs.models import Job, JobStatus, TaskStatus, JobResult, Task
from app.infrastructure.queue import get_queue
from app.logger import logger


class JobService:
    """Service for job management."""
    
    @staticmethod
    def submit_job(
        experiment_id: str,
        candidate_id: str,
        candidate_name: str,
        tasks: List[Task]
    ) -> Job:
        """Submit a new job to the queue."""
        job = Job(
            experiment_id=experiment_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            status=JobStatus.QUEUED,
            tasks=tasks,
            total_tasks=len(tasks)
        )
        
        queue = get_queue()
        if not queue.enqueue_job(job):
            raise RuntimeError(f"Failed to enqueue job {job.id}")
        
        logger.info(f"Job {job.id} submitted for {candidate_name}")
        return job
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Job]:
        """Get job by ID."""
        queue = get_queue()
        return queue.get_job(job_id)
    
    @staticmethod
    def update_job_status(job_id: str, status: JobStatus) -> bool:
        """Update job status."""
        queue = get_queue()
        job = queue.get_job(job_id)
        if not job:
            return False
        
        job.status = status
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in (JobStatus.COMPLETE, JobStatus.FAILED):
            job.completed_at = datetime.utcnow()
        
        return queue.update_job(job)
    
    @staticmethod
    def add_task_result(
        job_id: str,
        task_id: str,
        output: str,
        score: float,
        execution_time_ms: float,
        status: TaskStatus = TaskStatus.COMPLETE
    ) -> bool:
        """Add result for a completed task."""
        queue = get_queue()
        job = queue.get_job(job_id)
        if not job:
            return False
        
        job.results[task_id] = {
            "task_id": task_id,
            "output": output,
            "score": score,
            "execution_time_ms": execution_time_ms,
            "status": status.value,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        job.completed_tasks += 1
        return queue.update_job(job)
    
    @staticmethod
    def mark_job_failed(job_id: str, error_message: str) -> bool:
        """Mark job as failed."""
        queue = get_queue()
        job = queue.get_job(job_id)
        if not job:
            return False
        
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        
        return queue.update_job(job)


# Initialize service
job_service = JobService()