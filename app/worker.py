"""
Worker that pulls jobs from queue and executes them.

Worker loop:
  1. Dequeue job (task + candidate + repetition)
  2. Fetch task from database
  3. Get model adapter
  4. Call adapter.execute()
  5. Store execution results
  6. Mark job complete
  7. Repeat
"""

import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.queue import job_queue, Job
from app.models import Task, CandidateVersion, Execution, Experiment
from app.adapters import get_adapter, AdapterRequest, AdapterError
from app.logger import setup_logger

logger = setup_logger(__name__)

# Database connection for worker
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Worker:
    """
    Worker that executes benchmark tasks.
    
    Usage:
        worker = Worker(worker_id="worker-1", poll_interval=1.0)
        worker.run()  # Blocks, processes jobs indefinitely
    """
    
    def __init__(self, worker_id: str = "worker-1", poll_interval: float = 1.0):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique worker identifier
            poll_interval: Seconds to wait between queue polls
        """
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.running = False
        self.jobs_processed = 0
        self.jobs_failed = 0
        
        logger.info(f"Worker {worker_id} initialized (poll_interval={poll_interval}s)")
    
    def run(self, max_jobs: int = None):
        """
        Run worker (blocks until stopped).
        
        Args:
            max_jobs: Stop after processing N jobs (None = run forever)
        """
        self.running = True
        logger.info(f"Worker {self.worker_id} starting...")
        
        try:
            while self.running:
                # Check if we should stop
                if max_jobs and self.jobs_processed >= max_jobs:
                    logger.info(f"Worker {self.worker_id} reached max_jobs ({max_jobs})")
                    break
                
                # Try to get a job
                job = job_queue.dequeue(timeout=self.poll_interval)
                
                if job is None:
                    # No job available, wait and retry
                    continue
                
                logger.info(f"[{self.worker_id}] Processing job: {job.job_id}")
                
                try:
                    self._execute_job(job)
                    self.jobs_processed += 1
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Job execution failed: {str(e)}")
                    job_queue.fail(job.job_id, str(e))
                    self.jobs_failed += 1
        
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id} interrupted by user")
        finally:
            self.running = False
            self.stop()
    
    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        stats = job_queue.stats()
        logger.info(
            f"Worker {self.worker_id} stopped. "
            f"Processed: {self.jobs_processed}, Failed: {self.jobs_failed}, "
            f"Queue stats: {stats}"
        )
    
    def _execute_job(self, job: Job):
        """
        Execute a single job.
        
        Args:
            job: Job to execute
            
        Raises:
            Exception: If execution fails
        """
        db = SessionLocal()
        
        try:
            # 1. Fetch task from database
            task = db.query(Task).filter(Task.id == job.task_id).first()
            if not task:
                raise Exception(f"Task not found: {job.task_id}")
            
            # 2. Fetch candidate version
            candidate_version = db.query(CandidateVersion).filter(
                CandidateVersion.id == job.candidate_version_id
            ).first()
            if not candidate_version:
                raise Exception(f"Candidate version not found: {job.candidate_version_id}")
            
            # 3. Get adapter for this model
            adapter = get_adapter(candidate_version.config)
            
            # 4. Create adapter request
            request = AdapterRequest(
                task_id=task.task_id,
                problem_statement=task.problem_statement,
                public_tests=task.public_tests or [],
                temperature=candidate_version.config.get("temperature", 0.7),
                max_tokens=candidate_version.config.get("max_tokens", 2048)
            )
            
            logger.debug(f"[{self.worker_id}] Calling adapter: {candidate_version.model_id}")
            
            # 5. Execute on model (this calls the actual API)
            start_time = datetime.utcnow()
            response = adapter.execute(request)
            
            # 6. Create Execution record in database
            execution = Execution(
                experiment_id=job.experiment_id,
                task_id=job.task_id,
                candidate_version_id=job.candidate_version_id,
                repetition_number=job.repetition_number,
                status="complete",
                enqueued_at=job.created_at,
                started_at=job.started_at,
                completed_at=datetime.utcnow(),
                latency_ms=response.latency_ms,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=0.0,  # TODO: Calculate from adapter response
                model_response=response.response[:10000],  # Truncate if too long
                passed=None,  # TODO: Evaluate response
                score=None,  # TODO: Score response
                evaluation_details=None  # TODO: Add evaluation details
            )
            
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # 7. Mark job as complete
            result = {
                "execution_id": str(execution.id),
                "status": "complete",
                "latency_ms": response.latency_ms,
                "tokens": {
                    "input": response.input_tokens,
                    "output": response.output_tokens
                }
            }
            job_queue.complete(job.job_id, execution.id, result)
            
            # 8. Update experiment spent_usd
            experiment = db.query(Experiment).filter(
                Experiment.id == job.experiment_id
            ).first()
            if experiment:
                # TODO: Actually calculate cost
                experiment.spent_usd = 0.0
                db.commit()
            
            logger.info(
                f"[{self.worker_id}] Job completed: {job.job_id} "
                f"({response.latency_ms}ms, "
                f"{response.input_tokens} in, {response.output_tokens} out)"
            )
        
        except Exception as e:
            logger.error(f"[{self.worker_id}] Error executing job {job.job_id}: {str(e)}")
            raise
        
        finally:
            db.close()


def run_worker(worker_id: str = "worker-1", max_jobs: int = None):
    """
    Start a worker (blocking).
    
    Args:
        worker_id: Unique worker ID
        max_jobs: Stop after N jobs (for testing)
    """
    worker = Worker(worker_id=worker_id)
    worker.run(max_jobs=max_jobs)