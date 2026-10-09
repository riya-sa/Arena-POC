"""
FastAPI application entry point.
File: app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.logger import get_logger

# Import routers (will be created in app/api/v1/)
# from app.api.v1.benchmarks import benchmark_router
# from app.api.v1.candidates import candidate_router
# from app.api.v1.experiments import experiment_router
# from app.api.v1.health import health_router

logger = get_logger(__name__)


# ============================================================================
# Lifecycle Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Logging: {settings.log_format} format, {settings.log_level} level")
    
    await init_db()
    logger.info("✅ Application started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("✅ Application stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Private AI benchmarking and evaluation platform",
    docs_url="/api/docs" if settings.enable_debug_endpoints else None,
    redoc_url="/api/redoc" if settings.enable_debug_endpoints else None,
    lifespan=lifespan
)

logger.info(f"FastAPI app created: {settings.app_name} v{settings.app_version}")


# ============================================================================
# Middleware
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware configured")


# ============================================================================
# Routes
# ============================================================================

# Health check (always available)
@app.get("/api/v1/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for readiness/liveness probes.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment
    }


# Include v1 routers (will be uncommented once files exist)
# app.include_router(benchmark_router, prefix="/api/v1")
# app.include_router(candidate_router, prefix="/api/v1")
# app.include_router(experiment_router, prefix="/api/v1")
# app.include_router(health_router, prefix="/api/v1")

logger.info("✅ Routes configured")


# ============================================================================
# Error Handling (Middleware)
# ============================================================================

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.domain.shared.exceptions import ArenaException


@app.exception_handler(ArenaException)
async def arena_exception_handler(request, exc: ArenaException):
    """
    Handle domain exceptions and convert to HTTP responses.
    """
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """
    Catch unexpected errors and return safe response.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
    )


logger.info("✅ Error handlers configured")


# ============================================================================
# Development Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )