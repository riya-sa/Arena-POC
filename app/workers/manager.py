"""Manage worker processes."""

import asyncio
from typing import List, Optional
from app.workers.task_processor import TaskProcessor
from app.logger import logger


class WorkerManager:
    """Manages multiple worker instances."""
    
    def __init__(self, num_workers: int = 2, concurrency_per_worker: int = 4):
        """Initialize worker manager."""
        self.num_workers = num_workers
        self.concurrency_per_worker = concurrency_per_worker
        self.workers: List[TaskProcessor] = []
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start all workers."""
        logger.info(f"Starting {self.num_workers} workers")
        
        for i in range(self.num_workers):
            worker = TaskProcessor(
                worker_id=f"worker-{i+1}",
                concurrency=self.concurrency_per_worker
            )
            self.workers.append(worker)
            
            # Create and start worker task
            task = asyncio.create_task(worker.run())
            self.tasks.append(task)
            
            logger.info(f"Worker {i+1} started")
    
    async def stop(self):
        """Stop all workers gracefully."""
        logger.info("Stopping all workers")
        
        # Signal all workers to stop
        for worker in self.workers:
            worker.stop()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("All workers stopped")
    
    def get_stats(self) -> dict:
        """Get stats from all workers."""
        return {
            "num_workers": self.num_workers,
            "workers": [w.stats() for w in self.workers]
        }
    
    def is_running(self) -> bool:
        """Check if any worker is running."""
        return any(w.running for w in self.workers)


# Global worker manager
manager: Optional[WorkerManager] = None


def init_workers(num_workers: int = 2) -> WorkerManager:
    """Initialize global worker manager."""
    global manager
    manager = WorkerManager(num_workers=num_workers)
    return manager


def get_worker_manager() -> Optional[WorkerManager]:
    """Get global worker manager."""
    return manager