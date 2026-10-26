"""Worker process for executing tasks."""

import asyncio
import time
from typing import Optional
from datetime import datetime
from app.domain.jobs import JobStatus, TaskStatus, JobService
from app.infrastructure.queue import get_queue
from app.logger import logger
from app.adapters import get_adapter
from app.workers.retry_manager import get_retry_manager


class TaskProcessor:
    """Process jobs from queue and execute tasks."""
    
    def __init__(self, worker_id: str = "worker-1", concurrency: int = 4):
        """Initialize worker."""
        self.worker_id = worker_id
        self.concurrency = concurrency
        self.running = False
        self.processed_jobs = 0
        self.processed_tasks = 0
        self.errors = 0
    
    async def process_job(self, job_id: str) -> bool:
        """Process a single job."""
        try:
            # Get job from queue
            queue = get_queue()
            job = queue.get_job(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return False
            
            logger.info(f"{self.worker_id}: Processing job {job_id} ({job.candidate_name})")
            
            # Update status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            queue.update_job(job)
            
            # Get adapter for candidate
            adapter = get_adapter(job.candidate_id)
            if not adapter:
                logger.error(f"Adapter not found for {job.candidate_id}")
                JobService.mark_job_failed(job_id, "Adapter not found")
                return False
            
            # Process each task
            for task in job.tasks:
                result = await self.execute_task_with_retry(
                    job_id,
                    task.id,
                    task.input_data,
                    task.expected_output,
                    adapter
                )
                
                if not result['success']:
                    job.failed_tasks += 1
                    logger.warning(f"Task {task.id} failed: {result.get('error')}")
                else:
                    job.completed_tasks += 1
                    
                    # Save result to job
                    JobService.add_task_result(
                        job_id=job_id,
                        task_id=task.id,
                        output=result.get('output', ''),
                        score=result.get('score', 0.0),
                        execution_time_ms=result.get('execution_time_ms', 0.0)
                    )
            
            # Mark job complete
            job.status = JobStatus.COMPLETE
            job.completed_at = datetime.utcnow()
            queue.update_job(job)
            queue.mark_complete(job_id)
            
            logger.info(
                f"{self.worker_id}: Job {job_id} complete "
                f"({job.completed_tasks}/{job.total_tasks} tasks)"
            )
            self.processed_jobs += 1
            return True
            
        except Exception as e:
            logger.error(f"{self.worker_id}: Error processing job {job_id}: {str(e)}")
            JobService.mark_job_failed(job_id, str(e))
            self.errors += 1
            return False
    
    async def execute_task(
        self,
        job_id: str,
        task_id: str,
        input_data: str,
        expected_output: str,
        adapter
    ) -> dict:
        """Execute a single task with the adapter."""
        start_time = time.time()
        
        try:
            logger.debug(f"{self.worker_id}: Executing task {task_id}")
            
            # Call adapter (mock or real)
            output = await adapter.execute(input_data)
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Simple scoring: exact match
            score = 1.0 if output.strip() == expected_output.strip() else 0.0
            
            logger.debug(f"{self.worker_id}: Task {task_id} score: {score}")
            self.processed_tasks += 1
            
            return {
                "success": True,
                "output": output,
                "score": score,
                "execution_time_ms": execution_time_ms
            }
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"{self.worker_id}: Task {task_id} failed: {str(e)}")
            self.errors += 1
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms
            }
    async def execute_task_with_retry(
        self,
        job_id: str,
        task_id: str,
        input_data: str,
        expected_output: str,
        adapter
    ) -> dict:
       
        retry_mgr = get_retry_manager()
        policy = retry_mgr.policy
        
        for attempt in range(policy.max_retries + 1):
            try:
                result = await self.execute_task(
                    job_id, task_id, input_data, expected_output, adapter
                )
                
                if attempt > 0:
                    logger.info(f"Task {task_id} succeeded on retry {attempt}")
                
                return result
            
            except Exception as e:
                if attempt < policy.max_retries:
                    delay = policy.get_delay(attempt)
                    retry_mgr.record_retry(job_id, task_id, attempt + 1, str(e))
                    logger.warning(
                        f"Task {task_id} retry {attempt + 1}/{policy.max_retries + 1} "
                        f"in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    retry_mgr.record_retry(job_id, task_id, attempt + 1, str(e))
                    logger.error(f"Task {task_id} failed after {attempt + 1} attempts")
                    return {
                        "success": False,
                        "error": str(e),
                        "execution_time_ms": 0
                    }
                
    async def run(self):
        """Main worker loop - continuously process jobs."""
        self.running = True
        logger.info(f"{self.worker_id}: Starting (concurrency={self.concurrency})")
        
        while self.running:
            try:
                queue = get_queue()
                queue_length = queue.get_queue_length()
                
                if queue_length > 0:
                    logger.info(f"{self.worker_id}: Queue length: {queue_length}")
                    
                    # Process one job
                    job = queue.dequeue_job()
                    if job:
                        await self.process_job(job.id)
                    else:
                        await asyncio.sleep(1)
                else:
                    # No jobs, sleep briefly
                    await asyncio.sleep(2)
            
            except Exception as e:
                logger.error(f"{self.worker_id}: Error in main loop: {str(e)}")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop worker gracefully."""
        logger.info(f"{self.worker_id}: Stopping")
        self.running = False
    
    def stats(self) -> dict:
        """Get worker statistics."""
        return {
            "worker_id": self.worker_id,
            "processed_jobs": self.processed_jobs,
            "processed_tasks": self.processed_tasks,
            "errors": self.errors,
            "running": self.running
        }