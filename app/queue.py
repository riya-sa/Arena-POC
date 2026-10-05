"""
Job queue for benchmark task execution.

POC: Simple in-memory queue
Production: Replace with RabbitMQ, Kafka, or AWS SQS

Queue flow:
  1. Experiment submitted → Create job for each (task, candidate, repetition) combination
  2. Jobs enqueued → Added to queue
  3. Worker pulls jobs → Executes one by one
  4. Results stored → Job marked complete
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import queue
import threading

from app.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Job:
    """A single job: (task, candidate, repetition) to execute."""
    
    job_id: str  # Unique identifier
    experiment_id: UUID
    task_id: UUID
    candidate_version_id: UUID
    repetition_number: int
    
    # Execution state
    status: str = "queued"  # queued, running, completed, failed
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results (populated after execution)
    execution_id: Optional[UUID] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class JobQueue:
    """
    Simple in-memory job queue for POC.
    Thread-safe using queue.Queue.
    """
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize queue.
        
        Args:
            max_size: Maximum jobs in queue (0 = unlimited)
        """
        self._queue = queue.Queue(maxsize=max_size)
        self._jobs = {}  # job_id → Job (for tracking)
        self._lock = threading.Lock()
        
        logger.info(f"JobQueue initialized (max_size={max_size})")
    
    def enqueue(self, job: Job) -> str:
        """
        Add job to queue.
        
        Args:
            job: Job to enqueue
            
        Returns:
            Job ID
            
        Raises:
            queue.Full: If queue is full
        """
        try:
            self._queue.put(job, block=False)
            
            with self._lock:
                self._jobs[job.job_id] = job
            
            logger.debug(f"Job enqueued: {job.job_id} (experiment={job.experiment_id})")
            return job.job_id
            
        except queue.Full:
            logger.error(f"Queue is full! Cannot enqueue job {job.job_id}")
            raise
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[Job]:
        """
        Get next job from queue (blocks until available or timeout).
        
        Args:
            timeout: Seconds to wait (None = wait forever)
            
        Returns:
            Job or None if timeout
        """
        try:
            job = self._queue.get(timeout=timeout)
            job.status = "running"
            job.started_at = datetime.utcnow()
            
            logger.debug(f"Job dequeued: {job.job_id}")
            return job
            
        except queue.Empty:
            return None
    
    def complete(self, job_id: str, execution_id: UUID, result: dict):
        """
        Mark job as completed.
        
        Args:
            job_id: Job identifier
            execution_id: Execution ID from database
            result: Execution results
        """
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.execution_id = execution_id
                job.result = result
                
                logger.debug(f"Job completed: {job_id}")
    
    def fail(self, job_id: str, error: str):
        """
        Mark job as failed.
        
        Args:
            job_id: Job identifier
            error: Error message
        """
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                job.error = error
                
                logger.error(f"Job failed: {job_id} - {error}")
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def size(self) -> int:
        """Get number of jobs in queue."""
        return self._queue.qsize()
    
    def stats(self) -> dict:
        """Get queue statistics."""
        with self._lock:
            statuses = {"queued": 0, "running": 0, "completed": 0, "failed": 0}
            for job in self._jobs.values():
                statuses[job.status] = statuses.get(job.status, 0) + 1
            
            return {
                "total_jobs": len(self._jobs),
                "queue_size": self._queue.qsize(),
                "statuses": statuses
            }


# Global queue instance
job_queue = JobQueue()