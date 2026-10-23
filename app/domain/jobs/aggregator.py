"""Aggregate job results into experiment results."""

from typing import Dict, Any, List
from app.domain.jobs import JobService
from app.logger import logger


class ResultAggregator:
    """Aggregate results from multiple jobs."""
    
    @staticmethod
    def aggregate_experiment_results(experiment_id: str, jobs: List[str]) -> Dict[str, Any]:
        """Aggregate all job results for an experiment."""
        results = {
            "experiment_id": experiment_id,
            "candidates": {},
            "summary": {
                "total_jobs": len(jobs),
                "completed_jobs": 0,
                "failed_jobs": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0
            }
        }
        
        for job_id in jobs:
            job = JobService.get_job(job_id)
            if not job:
                continue
            
            candidate_key = job.candidate_name
            
            if candidate_key not in results["candidates"]:
                results["candidates"][candidate_key] = {
                    "jobs": [],
                    "total_score": 0.0,
                    "average_score": 0.0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "total_execution_time_ms": 0.0
                }
            
            # Add job results
            cand_data = results["candidates"][candidate_key]
            cand_data["jobs"].append({
                "job_id": job_id,
                "status": job.status.value,
                "completed_tasks": job.completed_tasks,
                "failed_tasks": job.failed_tasks,
                "results": job.results
            })
            
            # Update candidate stats
            cand_data["completed_tasks"] += job.completed_tasks
            cand_data["failed_tasks"] += job.failed_tasks
            
            # Calculate score
            job_results = job.results
            if job_results:
                scores = [r.get("score", 0.0) for r in job_results.values() if "score" in r]
                if scores:
                    job_score = sum(scores) / len(scores)
                    cand_data["total_score"] += job_score
                    cand_data["average_score"] = cand_data["total_score"] / len(cand_data["jobs"])
            
            # Update summary
            if job.status.value == "complete":
                results["summary"]["completed_jobs"] += 1
            else:
                results["summary"]["failed_jobs"] += 1
            
            results["summary"]["total_tasks"] += job.total_tasks
            results["summary"]["completed_tasks"] += job.completed_tasks
            results["summary"]["failed_tasks"] += job.failed_tasks
        
        return results