"""
Structured logging setup.
File: app/logger.py
"""

import logging
import sys
import json
from datetime import datetime, UTC
from typing import Any, Dict

from app.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    Outputs logs as JSON for easier parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Simple text formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format as readable text."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} [{record.levelname}] {record.name}: {record.getMessage()}"


def get_logger(name: str, extra: Dict[str, Any] = None) -> logging.Logger:
    """
    Get configured logger with JSON or text formatting.
    
    Args:
        name: Logger name (typically __name__)
        extra: Additional context to include in logs
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(settings.log_level)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(settings.log_level)
        
        # Set formatter based on config
        if settings.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter()
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    # Return logger (optionally with extra context)
    if extra:
        # Wrap logger to automatically add extra fields
        return _ExtraLoggerAdapter(logger, extra)
    
    return logger


class _ExtraLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds extra fields to all log messages.
    """
    
    def process(self, msg: str, kwargs: Dict) -> tuple:
        """Add extra context to all logs."""
        kwargs["extra"] = self.extra
        return msg, kwargs


# Module-level logger for this file
logger = get_logger(__name__)

logger.info(f"Logging configured: format={settings.log_format}, level={settings.log_level}")