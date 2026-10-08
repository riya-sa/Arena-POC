"""
app/shared/errors.py

Copy this file directly to: app/shared/errors.py
NO EDITING NEEDED
"""

from typing import Optional, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    """Base application error"""
    
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class ValidationError(ApplicationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("VALIDATION_ERROR", message, 400, details)


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__("AUTHENTICATION_REQUIRED", message, 401)


class PermissionError(ApplicationError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__("PERMISSION_DENIED", message, 403)


class NotFoundError(ApplicationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("NOT_FOUND", message, 404, details)


class ConflictError(ApplicationError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("CONFLICT", message, 409, details)


class RateLimitError(ApplicationError):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__("RATE_LIMITED", message, 429, {"retry_after": retry_after} if retry_after else {})


class InternalError(ApplicationError):
    def __init__(self, message: str = "Internal server error", details: Optional[dict] = None):
        super().__init__("INTERNAL_ERROR", message, 500, details)


class UnavailableError(ApplicationError):
    def __init__(self, message: str = "Service unavailable", retry_after: Optional[int] = None):
        super().__init__("UNAVAILABLE", message, 503, {"retry_after": retry_after} if retry_after else {})


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers"""
    
    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details if exc.details else None
                },
                "path": str(request.url.path),
                "method": request.method
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": None
                },
                "path": str(request.url.path)
            }
        )