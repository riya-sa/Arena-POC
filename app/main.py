"""
Week 11: Refactored Main Application Factory

Replace app/main.py with this cleaner version.

Key improvements:
- Factory pattern for testability
- Clean middleware setup
- Centralized exception handling
- Environment-aware configuration
- No circular imports
"""

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# from contextlib import asynccontextmanager

# from app.config.settings import settings
# from app.infrastructure.database import init_db, engine
# from app.shared.errors import register_exception_handlers
# from app.api.v1 import router as v1_router


# # ============================================================================
# # CUSTOM MIDDLEWARE
# # ============================================================================

# class RequestIdMiddleware:
#     """Add correlation ID to each request for tracing"""
    
#     def __init__(self, app):
#         self.app = app
    
#     async def __call__(self, scope, receive, send):
#         import uuid
#         import contextvars
        
#         if scope["type"] != "http":
#             await self.app(scope, receive, send)
#             return
        
#         request_id = str(uuid.uuid4())
        
#         # Store in context for access throughout request
#         from app.shared.context import request_id_var
#         request_id_var.set(request_id)
        
#         async def send_with_request_id(message):
#             if message["type"] == "http.response.start":
#                 headers = list(message.get("headers", []))
#                 headers.append((b"x-request-id", request_id.encode()))
#                 message["headers"] = headers
            
#             await send(message)
        
#         await self.app(scope, receive, send_with_request_id)


# class HealthCheckMiddleware:
#     """Skip processing for /health endpoint"""
    
#     def __init__(self, app):
#         self.app = app
    
#     async def __call__(self, scope, receive, send):
#         # Let FastAPI handle it normally
#         await self.app(scope, receive, send)


# # ============================================================================
# # LIFESPAN MANAGEMENT (FastAPI 0.93+)
# # ============================================================================

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Manage application startup and shutdown
    
#     FastAPI 0.93+ uses asynccontextmanager instead of on_event
#     """
    
#     # Startup
#     print("\n" + "="*70)
#     print("🚀 Starting C/AI Arena Optimization")
#     print("="*70)
    
#     print(f"Environment: {settings.environment}")
#     print(f"Debug mode: {settings.debug}")
#     print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'unknown'}")
    
#     # Initialize database
#     try:
#         init_db()
#         print("✅ Database initialized")
#     except Exception as e:
#         print(f"❌ Database initialization failed: {e}")
#         raise
    
#     print(f"🔗 API running at {settings.api_base_url}")
#     print("="*70 + "\n")
    
#     yield  # Application runs here
    
#     # Shutdown
#     print("\n" + "="*70)
#     print("🛑 Shutting down C/AI Arena Optimization")
#     print("="*70)
    
#     # Cleanup
#     try:
#         engine.dispose()
#         print("✅ Database connections closed")
#     except Exception as e:
#         print(f"⚠️  Error closing database: {e}")
    
#     print("="*70 + "\n")


# # ============================================================================
# # APPLICATION FACTORY
# # ============================================================================

# def create_app() -> FastAPI:
#     """
#     Factory function for FastAPI application
    
#     Allows creating multiple app instances for testing
#     """
    
#     app = FastAPI(
#         title=settings.api_title,
#         version=settings.api_version,
#         debug=settings.debug,
#         # Hide OpenAPI docs in production (security)
#         docs_url="/api/docs" if settings.debug else None,
#         redoc_url="/api/redoc" if settings.debug else None,
#         openapi_url="/api/openapi.json" if settings.debug else None,
#         # Lifespan management
#         lifespan=lifespan
#     )
    
#     # ========================================================================
#     # MIDDLEWARE
#     # ========================================================================
    
#     # Trust headers from reverse proxy (load balancer)
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=settings.allowed_hosts
#     )
    
#     # CORS for frontend
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=settings.cors_origins,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
    
#     # Custom middleware
#     app.add_middleware(RequestIdMiddleware)
    
#     # ========================================================================
#     # EXCEPTION HANDLERS
#     # ========================================================================
    
#     register_exception_handlers(app)
    
#     # ========================================================================
#     # ROUTES
#     # ========================================================================
    
#     # Health check (no auth required)
#     @app.get("/health", tags=["health"])
#     def health():
#         """Health check endpoint for load balancers"""
#         return {
#             "status": "ok",
#             "environment": settings.environment,
#             "version": settings.api_version
#         }
    
#     # API v1 routes
#     app.include_router(
#         v1_router,
#         tags=["v1"]
#     )
    
#     # ========================================================================
#     # ROOT ENDPOINT
#     # ========================================================================
    
#     @app.get("/", tags=["info"])
#     def root():
#         """API information"""
#         return {
#             "title": settings.api_title,
#             "version": settings.api_version,
#             "environment": settings.environment,
#             "docs": "/api/docs" if settings.debug else None,
#             "health": "/health"
#         }
    
#     # ========================================================================
#     # 404 HANDLER
#     # ========================================================================
    
#     @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
#     async def not_found(path_name: str):
#         """Handle 404s with helpful error message"""
#         from app.shared.errors import NotFoundError
#         raise NotFoundError(
#             f"Endpoint /{path_name} not found",
#             details={
#                 "available_endpoints": [
#                     "/v1/benchmarks",
#                     "/v1/candidates",
#                     "/v1/experiments",
#                     "/v1/results",
#                     "/health",
#                     "/api/docs"
#                 ]
#             }
#         )
    
#     return app


# # ============================================================================
# # MODULE-LEVEL APP INSTANCE
# # ============================================================================

# # Create the app instance for production
# app = create_app()


# # ============================================================================
# # TESTING
# # ============================================================================

# def get_test_app() -> FastAPI:
#     """
#     Create app instance for testing
    
#     Usage in tests:
#         from app.main import get_test_app
#         from fastapi.testclient import TestClient
        
#         client = TestClient(get_test_app())
#         response = client.get("/health")
#     """
#     return create_app()


# # ============================================================================
# # RUNNING THE APP
# # ============================================================================

# if __name__ == "__main__":
#     import uvicorn
    
#     uvicorn.run(
#         "app.main:app",
#         host=settings.api_host,
#         port=settings.api_port,
#         reload=settings.debug,
#         log_level=settings.log_level.lower(),
#         access_log=not settings.debug,  # Disable access logs in debug
#     )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.shared.errors import register_exception_handlers
from app.api.v1 import router as v1_router


def create_app() -> FastAPI:
    """Create and configure FastAPI app"""
    
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    register_exception_handlers(app)
    
    # Health check
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    # Include API routers
    app.include_router(v1_router)
    
    return app


# Create app instance
app = create_app()