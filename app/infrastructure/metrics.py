"""Collect and report metrics."""

from datetime import datetime, timedelta
from typing import Dict, List
from app.logger import logger


class MetricsCollector:
    """Collect execution metrics."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.jobs_submitted = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time_ms = 0.0
        self.errors: List[dict] = []
    
    def record_job_submitted(self):
        """Record job submission."""
        self.jobs_submitted += 1
    
    def record_job_completed(self, execution_time_ms: float):
        """Record completed job."""
        self.jobs_completed += 1
        self.total_execution_time_ms += execution_time_ms
    
    def record_job_failed(self):
        """Record failed job."""
        self.jobs_failed += 1
    
    def record_task_completed(self):
        """Record completed task."""
        self.tasks_completed += 1
    
    def record_task_failed(self, error: str):
        """Record failed task."""
        self.tasks_failed += 1
        self.errors.append({
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_metrics(self) -> Dict:
        """Get current metrics."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "jobs": {
                "submitted": self.jobs_submitted,
                "completed": self.jobs_completed,
                "failed": self.jobs_failed,
                "success_rate": self.jobs_completed / self.jobs_submitted if self.jobs_submitted > 0 else 0
            },
            "tasks": {
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "success_rate": self.tasks_completed / (self.tasks_completed + self.tasks_failed) if (self.tasks_completed + self.tasks_failed) > 0 else 0
            },
            "performance": {
                "avg_job_time_ms": self.total_execution_time_ms / self.jobs_completed if self.jobs_completed > 0 else 0,
                "total_execution_time_ms": self.total_execution_time_ms
            },
            "errors": self.errors[-10:]  # Last 10 errors
        }


# Global metrics collector
metrics_collector = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return metrics_collector