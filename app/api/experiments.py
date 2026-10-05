"""
Experiment management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.database import get_db
from app.models import (
    Experiment, Execution, BenchmarkVersion, Task, CandidateVersion
)
from app.schemas import ExperimentCreate, ExperimentResponse, ExperimentDetailResponse, ExecutionResponse
from app.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    exp_request: ExperimentCreate,
    db: Session = Depends(get_db)
):
    """
    Create and submit a benchmark experiment.
    
    This creates jobs for every combination of:
    - Tasks in the benchmark
    - Candidate versions to compare
    - Repetitions
    
    Example:
    {
        "benchmark_version_id": "uuid",
        "candidate_version_ids": ["uuid1", "uuid2"],
        "name": "Claude vs GPT-4 comparison",
        "repetitions": 3,
        "budget_usd": 50.0
    }
    """
    try:
        logger.info(
            f"Creating experiment: {exp_request.name} "
            f"({len(exp_request.candidate_version_ids)} candidates, "
            f"{exp_request.repetitions} reps)"
        )
        
        # Verify benchmark version exists
        benchmark = db.query(BenchmarkVersion).filter(
            BenchmarkVersion.id == exp_request.benchmark_version_id
        ).first()
        
        if not benchmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Benchmark version not found: {exp_request.benchmark_version_id}"
            )
        
        # Verify all candidate versions exist
        candidates = db.query(CandidateVersion).filter(
            CandidateVersion.id.in_(exp_request.candidate_version_ids)
        ).all()
        
        if len(candidates) != len(exp_request.candidate_version_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some candidate versions not found"
            )
        
        # Create experiment
        experiment = Experiment(
            id=uuid.uuid4(),
            benchmark_version_id=exp_request.benchmark_version_id,
            name=exp_request.name or f"Experiment {uuid.uuid4().hex[:8]}",
            status="created",
            repetitions=exp_request.repetitions,
            budget_usd=exp_request.budget_usd,
            spent_usd=0
        )
        
        db.add(experiment)
        db.flush()
        
        # Get all tasks in this benchmark version
        tasks = db.query(Task).filter(
            Task.benchmark_version_id == exp_request.benchmark_version_id
        ).all()
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Benchmark has no tasks: {exp_request.benchmark_version_id}"
            )
        
        logger.info(f"Experiment {experiment.id} has {len(tasks)} tasks")
        
        # Create Execution record for each (task, candidate, repetition) combination
        # Status starts as "queued" - worker will pick these up from database
        execution_count = 0
        for task in tasks:
            for candidate_id in exp_request.candidate_version_ids:
                for rep in range(1, exp_request.repetitions + 1):
                    execution = Execution(
                        id=uuid.uuid4(),
                        experiment_id=experiment.id,
                        task_id=task.id,
                        candidate_version_id=candidate_id,
                        repetition_number=rep,
                        status="queued",  # Worker will pick this up
                        enqueued_at=datetime.utcnow()
                    )
                    
                    try:
                        db.add(execution)
                        execution_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create execution: {str(e)}")
                        db.rollback()
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create executions: {str(e)}"
                        )
        
        # Update status to queued
        experiment.status = "queued"
        db.commit()
        db.refresh(experiment)
        
        logger.info(f"Experiment created: {experiment.id} with {execution_count} executions")
        
        return experiment
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create experiment: {str(e)}"
        )


@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(db: Session = Depends(get_db)):
    """
    List all experiments.
    """
    try:
        experiments = db.query(Experiment).order_by(Experiment.submitted_at.desc()).all()
        logger.info(f"Listed {len(experiments)} experiments")
        return experiments
    except Exception as e:
        logger.error(f"Error listing experiments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list experiments"
        )


@router.get("/experiments/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific experiment with stats.
    """
    try:
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment not found: {experiment_id}"
            )
        
        # Get execution stats
        executions = db.query(Execution).filter(
            Execution.experiment_id == experiment_id
        ).all()
        
        completed = sum(1 for e in executions if e.status == "complete")
        failed = sum(1 for e in executions if e.status == "failed")
        
        logger.info(f"Retrieved experiment: {experiment_id}")
        
        # Return with stats
        response = ExperimentDetailResponse(
            id=experiment.id,
            status=experiment.status,
            name=experiment.name,
            repetitions=experiment.repetitions,
            budget_usd=experiment.budget_usd,
            spent_usd=experiment.spent_usd,
            submitted_at=experiment.submitted_at,
            started_at=experiment.started_at,
            completed_at=experiment.completed_at,
            error_message=experiment.error_message,
            total_executions=len(executions),
            completed_executions=completed,
            failed_executions=failed
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve experiment"
        )


@router.get("/experiments/{experiment_id}/executions", response_model=List[ExecutionResponse])
async def list_experiment_executions(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """
    List all executions for an experiment.
    """
    try:
        # Verify experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment not found: {experiment_id}"
            )
        
        executions = db.query(Execution).filter(
            Execution.experiment_id == experiment_id
        ).order_by(Execution.created_at.desc()).all()
        
        logger.info(f"Listed {len(executions)} executions for experiment {experiment_id}")
        return executions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list executions"
        )


@router.get("/queue/stats", response_model=dict)
async def get_queue_stats():
    """
    Get current job queue statistics.
    """
    return job_queue.stats()


@router.post("/experiments/{experiment_id}/cancel", response_model=ExperimentResponse)
async def cancel_experiment(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel an experiment (mark as cancelled).
    """
    try:
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment not found: {experiment_id}"
            )
        
        if experiment.status in ["complete", "failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel experiment with status: {experiment.status}"
            )
        
        experiment.status = "cancelled"
        db.commit()
        db.refresh(experiment)
        
        logger.info(f"Experiment cancelled: {experiment_id}")
        return experiment
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel experiment"
        )