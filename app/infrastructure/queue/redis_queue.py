"""Redis-based job queue implementation."""

import json
import redis
from typing import Optional, List
from datetime import datetime
from app.domain.jobs.models import Job, JobStatus, JobQueue
from app.logger import logger


class RedisJobQueue:
    """Manages job queue using Redis."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.queue_key = "arena:jobs:queue"
        self.job_prefix = "arena:job:"
        self.active_prefix = "arena:active:job:"
        
    def is_ready(self) -> bool:
        """Check if Redis is ready."""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis not ready: {str(e)}")
            return False
    
    def enqueue_job(self, job: Job) -> bool:
        """Add job to queue."""
        try:
            # Store job data
            self.redis_client.set(
                f"{self.job_prefix}{job.id}",
                job.to_json(),
                ex=86400  # 24 hour expiry
            )
            
            # Add to queue
            queue_item = JobQueue(
                job_id=job.id,
                experiment_id=job.experiment_id,
                candidate_id=job.candidate_id
            )
            self.redis_client.lpush(
                self.queue_key,
                json.dumps({
                    "job_id": queue_item.job_id,
                    "experiment_id": queue_item.experiment_id,
                    "timestamp": queue_item.timestamp.isoformat()
                })
            )
            
            logger.info(f"Job {job.id} enqueued")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue job: {str(e)}")
            return False
    
    def dequeue_job(self) -> Optional[Job]:
        """Get next job from queue."""
        try:
            queue_item_json = self.redis_client.rpop(self.queue_key)
            if not queue_item_json:
                return None
            
            queue_item = json.loads(queue_item_json)
            job_id = queue_item['job_id']
            
            # Fetch job data
            job_json = self.redis_client.get(f"{self.job_prefix}{job_id}")
            if not job_json:
                logger.warning(f"Job {job_id} not found in Redis")
                return None
            
            job = Job.from_json(job_json)
            
            # Mark as active
            self.redis_client.set(
                f"{self.active_prefix}{job_id}",
                "1",
                ex=3600  # 1 hour timeout
            )
            
            logger.info(f"Job {job_id} dequeued")
            return job
        except Exception as e:
            logger.error(f"Failed to dequeue job: {str(e)}")
            return None
    
    def update_job(self, job: Job) -> bool:
        """Update job status."""
        try:
            self.redis_client.set(
                f"{self.job_prefix}{job.id}",
                job.to_json(),
                ex=86400
            )
            logger.debug(f"Job {job.id} updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update job: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID."""
        try:
            job_json = self.redis_client.get(f"{self.job_prefix}{job_id}")
            if not job_json:
                return None
            return Job.from_json(job_json)
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    def mark_complete(self, job_id: str) -> bool:
        """Mark job as complete."""
        try:
            self.redis_client.delete(f"{self.active_prefix}{job_id}")
            logger.info(f"Job {job_id} marked complete")
            return True
        except Exception as e:
            logger.error(f"Failed to mark job complete: {str(e)}")
            return False
    
    def get_queue_length(self) -> int:
        """Get number of jobs in queue."""
        return self.redis_client.llen(self.queue_key)
    
    def get_active_jobs(self) -> List[str]:
        """Get all active job IDs."""
        keys = self.redis_client.keys(f"{self.active_prefix}*")
        return [key.replace(self.active_prefix, "") for key in keys]
    
    def clear_queue(self) -> bool:
        """Clear entire queue (dev only)."""
        try:
            self.redis_client.delete(self.queue_key)
            logger.warning("Queue cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {str(e)}")
            return False


# Global queue instance
job_queue: Optional[RedisJobQueue] = None


def init_queue(host: str = "localhost", port: int = 6379) -> RedisJobQueue:
    """Initialize global job queue."""
    global job_queue
    job_queue = RedisJobQueue(host=host, port=port)
    
    if not job_queue.is_ready():
        raise RuntimeError("Redis queue not available")
    
    logger.info("Job queue initialized")
    return job_queue


def get_queue() -> RedisJobQueue:
    """Get global job queue instance."""
    if job_queue is None:
        raise RuntimeError("Queue not initialized")
    return job_queue