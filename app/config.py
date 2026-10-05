"""
Configuration management for C/AI Arena POC
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://arena_user:arena_password@localhost:5432/arena_poc"
    DATABASE_ECHO: bool = True
    
    # API
    API_TITLE: str = "C/AI Arena POC"
    API_VERSION: str = "0.1.0"
    
    # Logging
    LOG_FILE: str = "logs/arena.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()