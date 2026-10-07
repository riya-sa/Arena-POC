from pydantic_settings import BaseSettings
from typing import Literal
import os

class Settings(BaseSettings):
    """Production settings with environment validation"""
    
    # Environment
    environment: Literal["development", "staging", "production"] = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    
    # API
    api_title: str = "C/AI Arena Optimization"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/arena")
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_pre_ping: bool = True  # Verify connections
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-in-production")
    cors_origins: list[str] = ["http://localhost:3000"]
    
    # Workers
    worker_timeout_seconds: int = 30
    worker_max_retries: int = 3
    worker_backoff_multiplier: float = 2.0
    
    # Features
    mock_adapters_enabled: bool = environment != "production"  # CRITICAL: Mock disabled in prod
    
    # Observability
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    trace_sample_rate: float = 0.1 if environment == "production" else 1.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Validate production constraints
if settings.environment == "production":
    if settings.debug:
        raise ValueError("Debug mode cannot be enabled in production")
    if settings.mock_adapters_enabled:
        raise ValueError("Mock adapters cannot be enabled in production")
    if settings.secret_key == "change-in-production":
        raise ValueError("SECRET_KEY must be set in production")