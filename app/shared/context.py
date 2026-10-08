import uuid
from contextvars import ContextVar

# Context variable for tracking request IDs across async operations
request_id_var: ContextVar[str] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())


def get_request_id() -> str:
    """Get current request ID from context"""
    request_id = request_id_var.get()
    if not request_id:
        request_id = generate_request_id()
        request_id_var.set(request_id)
    return request_id


def set_request_id(request_id: str) -> None:
    """Set request ID in context"""
    request_id_var.set(request_id)