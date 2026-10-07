from typing import Optional

class ApplicationError(Exception):
    """Base application error"""
    
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class ValidationError(ApplicationError):
    def __init__(self, message: str):
        super().__init__("VALIDATION_ERROR", message, 400)

class PermissionError(ApplicationError):
    def __init__(self, message: str):
        super().__init__("PERMISSION_DENIED", message, 403)

class NotFoundError(ApplicationError):
    def __init__(self, message: str):
        super().__init__("NOT_FOUND", message, 404)

class ConflictError(ApplicationError):
    def __init__(self, message: str):
        super().__init__("CONFLICT", message, 409)

# Exception handlers for FastAPI
from fastapi.responses import JSONResponse

async def application_error_handler(request, exc: ApplicationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message}
    )