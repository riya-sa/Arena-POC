"""
Candidate (model) management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.models import Candidate, CandidateVersion
from app.adapters import get_adapter, AdapterError
from app.schemas import CandidateCreate, CandidateResponse, CandidateVersionResponse
from app.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new model candidate.
    
    Supported providers:
    - "mock": Mock adapter (for testing, no API key needed)
    - "openai": GPT-4, GPT-4o (requires API key)
    - "anthropic": Claude (requires API key)
    - "local": Llama, Mistral (requires local inference server)
    
    Example:
    {
        "name": "GPT-4",
        "provider": "openai",
        "description": "OpenAI GPT-4 model",
        "version": {
            "version_number": "1.0",
            "model_id": "gpt-4",
            "config": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "input_price_per_1k_tokens": 0.01,
                "output_price_per_1k_tokens": 0.03
            }
        }
    }
    """
    try:
        logger.info(f"Creating candidate: {candidate.name} (provider: {candidate.provider})")
        
        # Create candidate
        cand = Candidate(
            id=uuid.uuid4(),
            name=candidate.name,
            provider=candidate.provider,
            description=candidate.description
        )
        db.add(cand)
        db.flush()
        
        # Create initial version
        version_config = {
            "provider": candidate.provider,
            **candidate.version.config
        }
        version = CandidateVersion(
            id=uuid.uuid4(),
            candidate_id=cand.id,
            version_number=candidate.version.version_number,
            model_id=candidate.version.model_id,
            config=version_config,
            status="active"
        )
        db.add(version)
        db.flush()
        
        # Test health check with adapter
        try:
            adapter = get_adapter(version_config)
            is_healthy = adapter.health_check()
            
            if not is_healthy:
                logger.warning(f"Health check failed for {candidate.name}, but registering anyway")
        except Exception as e:
            logger.warning(f"Could not verify health for {candidate.name}: {str(e)}")
            # Don't block registration on health check
        
        db.commit()
        db.refresh(cand)
        
        logger.info(f"Candidate created: {cand.id}")
        return cand
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create candidate: {str(e)}"
        )


@router.get("/candidates", response_model=List[CandidateResponse])
async def list_candidates(db: Session = Depends(get_db)):
    """
    List all registered model candidates with their versions.
    """
    try:
        candidates = db.query(Candidate).all()
        logger.info(f"Listed {len(candidates)} candidates")
        return candidates
    except Exception as e:
        logger.error(f"Error listing candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list candidates"
        )


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific candidate with all versions.
    """
    try:
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found"
            )
        
        logger.info(f"Retrieved candidate: {candidate_id}")
        return candidate
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidate"
        )


@router.post("/candidates/{candidate_id}/health", response_model=dict)
async def check_candidate_health(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if a candidate model is healthy and reachable.
    """
    try:
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found"
            )
        
        # Get latest active version
        version = db.query(CandidateVersion).filter(
            CandidateVersion.candidate_id == candidate_id,
            CandidateVersion.status == "active"
        ).order_by(CandidateVersion.created_at.desc()).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active version for candidate {candidate_id}"
            )
        
        # Test with adapter
        try:
            adapter = get_adapter(version.config)
            is_healthy = adapter.health_check()
            
            logger.info(f"Health check for {candidate.name}: {'OK' if is_healthy else 'FAILED'}")
            
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "healthy": is_healthy,
                "model_id": version.model_id,
                "provider": candidate.provider
            }
        except Exception as e:
            logger.error(f"Health check error for {candidate.name}: {str(e)}")
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "healthy": False,
                "error": str(e),
                "provider": candidate.provider
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check health"
        )


@router.get("/candidates/{candidate_id}/cost-estimate", response_model=dict)
async def estimate_candidate_cost(
    candidate_id: str,
    task_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Estimate cost for running a task on this candidate.
    
    Query params:
    - task_id: Optional task ID (for context)
    """
    try:
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found"
            )
        
        # Get latest active version
        version = db.query(CandidateVersion).filter(
            CandidateVersion.candidate_id == candidate_id,
            CandidateVersion.status == "active"
        ).order_by(CandidateVersion.created_at.desc()).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active version for candidate {candidate_id}"
            )
        
        # Estimate cost with adapter
        try:
            from app.adapters import AdapterRequest
            
            adapter = get_adapter(version.config)
            request = AdapterRequest(
                task_id=task_id or "sample",
                problem_statement="Sample problem for cost estimation"
            )
            estimated_cost = adapter.estimate_cost(request)
            
            logger.info(f"Cost estimate for {candidate.name}: ${estimated_cost:.6f}")
            
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "model_id": version.model_id,
                "estimated_cost_usd": round(estimated_cost, 6),
                "provider": candidate.provider
            }
        except Exception as e:
            logger.error(f"Cost estimation error for {candidate.name}: {str(e)}")
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "estimated_cost_usd": 0.0,
                "error": str(e),
                "provider": candidate.provider
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate cost"
        )


@router.post("/candidates/{candidate_id}/versions", response_model=CandidateVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate_version(
    candidate_id: str,
    version_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new version of a candidate model.
    
    Example:
    {
        "version_number": "1.1",
        "model_id": "gpt-4-turbo",
        "config": {
            "temperature": 0.8,
            "max_tokens": 4096
        }
    }
    """
    try:
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found"
            )
        
        version = CandidateVersion(
            id=uuid.uuid4(),
            candidate_id=candidate_id,
            version_number=version_data.get("version_number"),
            model_id=version_data.get("model_id"),
            config={
                "provider": candidate.provider,
                **version_data.get("config", {})
            },
            status="active"
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        logger.info(f"Created version {version.version_number} for candidate {candidate_id}")
        return version
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/candidates/{candidate_id}/versions", response_model=List[CandidateVersionResponse])
async def list_candidate_versions(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """
    List all versions of a candidate.
    """
    try:
        versions = db.query(CandidateVersion).filter(
            CandidateVersion.candidate_id == candidate_id
        ).order_by(CandidateVersion.created_at.desc()).all()
        
        logger.info(f"Listed {len(versions)} versions for candidate {candidate_id}")
        return versions
        
    except Exception as e:
        logger.error(f"Error listing versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list versions"
        )