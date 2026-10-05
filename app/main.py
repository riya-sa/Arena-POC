# """
# C/AI Arena - Main FastAPI Application
# POC Phase - Benchmark Evaluation Platform
# """

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import logging

# from app.config import settings
# from app.logger import setup_logger
# from app.database import engine, Base, get_db
# from app.api.benchmarks import router as benchmark_router

# # Setup logging
# logger = setup_logger(__name__)

# # Create tables
# logger.info("Creating database tables...")
# Base.metadata.create_all(bind=engine)
# logger.info("Database tables created successfully")

# # Create FastAPI app
# app = FastAPI(
#     title="C/AI Arena POC",
#     description="Private AI Model Benchmarking Platform",
#     version="0.1.0"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(benchmark_router, prefix="/api/v1", tags=["benchmarks"])

# # Health check
# @app.get("/health")
# async def health_check():
#     """Health check endpoint."""
#     return {
#         "status": "healthy",
#         "service": "arena-poc",
#         "environment": settings.ENVIRONMENT
#     }

# # Root endpoint
# @app.get("/")
# async def root():
#     """Root endpoint."""
#     return {
#         "message": "C/AI Arena POC API",
#         "version": "0.1.0",
#         "docs": "/docs"
#     }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         log_level=settings.LOG_LEVEL.lower()
#     )

"""
C/AI Arena - Main FastAPI Application
POC Phase - Benchmark Evaluation Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.logger import setup_logger
from app.database import engine, Base, get_db
from app.api.benchmarks import router as benchmark_router
from app.api.candidates import router as candidate_router

# Setup logging
logger = setup_logger(__name__)

# Create tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# Create FastAPI app
app = FastAPI(
    title="C/AI Arena POC",
    description="Private AI Model Benchmarking Platform",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(benchmark_router, prefix="/api/v1", tags=["benchmarks"])
app.include_router(candidate_router, prefix="/api/v1", tags=["candidates"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "arena-poc",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "C/AI Arena POC API",
        "version": "0.1.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )