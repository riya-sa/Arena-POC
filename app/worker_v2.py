"""
Worker v2 - Uses database for job storage (fixes cross-process issue).

This worker queries the database for jobs instead of using in-memory queue.
Works correctly when API and worker are separate processes.
"""

import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Task, CandidateVersion, Execution, Experiment
from app.adapters import get_adapter, AdapterRequest
from app.logger import setup_logger

logger = setup_logger(__name__)

# Database connection for worker
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Worker:
    """
    Worker that executes benchmark tasks.
    Queries database for jobs (fixes cross-process issue).
    """
    
    def __init__(self, worker_id: str = "worker-1", poll_interval: float = 1.0):
        """Initialize worker."""
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.running = False
        self.jobs_processed = 0
        self.jobs_failed = 0
        
        logger.info(f"Worker {worker_id} initialized (poll_interval={poll_interval}s)")
    
    def run(self, max_jobs: int = None):
        """Run worker (blocks until stopped)."""
        self.running = True
        logger.info(f"Worker {self.worker_id} starting...")
        
        try:
            while self.running:
                # Check if we should stop
                if max_jobs and self.jobs_processed >= max_jobs:
                    logger.info(f"Worker {self.worker_id} reached max_jobs ({max_jobs})")
                    break
                
                # Try to get a job from database
                db = SessionLocal()
                try:
                    # Find a queued execution
                    execution = db.query(Execution).filter(
                        Execution.status == "queued"
                    ).first()
                    
                    if execution is None:
                        # No jobs available, wait and retry
                        db.close()
                        time.sleep(self.poll_interval)
                        continue
                    
                    logger.info(
                        f"[{self.worker_id}] Processing execution: {execution.id} "
                        f"(task={execution.task_id}, candidate={execution.candidate_version_id})"
                    )
                    
                    # Mark as running
                    execution.status = "running"
                    execution.started_at = datetime.utcnow()
                    db.commit()
                    
                    # Execute
                    self._execute_execution(db, execution)
                    self.jobs_processed += 1
                    
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Execution failed: {str(e)}")
                    if execution:
                        execution.status = "failed"
                        execution.error_message = str(e)
                        execution.completed_at = datetime.utcnow()
                        db.commit()
                    self.jobs_failed += 1
                finally:
                    db.close()
        
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id} interrupted by user")
        finally:
            self.running = False
            self.stop()
    
    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        logger.info(
            f"Worker {self.worker_id} stopped. "
            f"Processed: {self.jobs_processed}, Failed: {self.jobs_failed}"
        )
    
    def _execute_execution(self, db, execution):
        """Execute a single execution from database."""
        try:
            # 1. Fetch task
            task = db.query(Task).filter(Task.id == execution.task_id).first()
            if not task:
                raise Exception(f"Task not found: {execution.task_id}")
            
            # 2. Fetch candidate version
            candidate_version = db.query(CandidateVersion).filter(
                CandidateVersion.id == execution.candidate_version_id
            ).first()
            if not candidate_version:
                raise Exception(f"Candidate version not found: {execution.candidate_version_id}")
            
            # 3. Get adapter
            adapter = get_adapter(candidate_version.config)
            
            # 4. Create request
            request = AdapterRequest(
                task_id=task.task_id,
                problem_statement=task.problem_statement,
                public_tests=task.public_tests or [],
                temperature=candidate_version.config.get("temperature", 0.7),
                max_tokens=candidate_version.config.get("max_tokens", 2048)
            )
            
            logger.debug(f"[{self.worker_id}] Calling adapter: {candidate_version.model_id}")
            
            # 5. Execute
            response = adapter.execute(request)
            
            # 6. Update execution with results
            execution.status = "complete"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = response.latency_ms
            execution.input_tokens = response.input_tokens
            execution.output_tokens = response.output_tokens
            execution.cost_usd = 0.0  # TODO: Calculate from tokens
            execution.model_response = response.response[:10000]  # Truncate if too long
            execution.passed = None  # TODO: Evaluate
            execution.score = None  # TODO: Score
            
            db.commit()
            
            logger.info(
                f"[{self.worker_id}] Execution completed: {execution.id} "
                f"({response.latency_ms}ms, {response.input_tokens} in, {response.output_tokens} out)"
            )
        
        except Exception as e:
            logger.error(f"[{self.worker_id}] Error: {str(e)}")
            raise


def run_worker(worker_id: str = "worker-1", max_jobs: int = None):
    """Start a worker (blocking)."""
    worker = Worker(worker_id=worker_id)
    worker.run(max_jobs=max_jobs)