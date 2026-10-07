from fastapi import FastAPI
from app.config.settings import settings
from app.api.v1 import router as v1_router
from app.infrastructure.database import init_db

def create_app() -> FastAPI:
    """Factory for FastAPI application"""
    
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug,
        docs_url="/api/docs" if settings.debug else None,  # Hide docs in prod
    )
    
    # Middleware
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins)
    app.add_middleware(RequestIdMiddleware)  # Add correlation IDs
    
    # Initialize database
    init_db()
    
    # Routes
    app.include_router(v1_router)
    
    # Health check
    @app.get("/health")
    def health():
        return {"status": "ok", "environment": settings.environment}
    
    return app

app = create_app()