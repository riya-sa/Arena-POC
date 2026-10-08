#  app/config.py (Production)
from pydantic import BaseSettings, Field, validator
from enum import Enum
from typing import List, Optional

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    app_name: str = "C/AI Arena Optimization"
    app_version: str = Field("1.0.0", env="APP_VERSION")
    environment: Environment = Field(Environment.DEVELOPMENT, env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")  # Required
    database_pool_size: int = Field(20, env="DATABASE_POOL_SIZE")
    database_echo: bool = False
    
    # Authentication
    auth_enabled: bool = Field(True, env="AUTH_ENABLED")
    oidc_issuer: Optional[str] = Field(None, env="OIDC_ISSUER")
    
    # Adapter
    adapter_type: str = Field("openai", env="ADAPTER_TYPE")
    
    # Queue
    queue_type: str = Field("database", env="QUEUE_TYPE")
    queue_polling_interval_ms: int = 1000
    
    # Observability
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    opentelemetry_enabled: bool = Field(True, env="OPENTELEMETRY_ENABLED")
    
    # Security
    enable_mock_adapters: bool = Field(False, env="ENABLE_MOCK_ADAPTERS")
    enable_debug_endpoints: bool = Field(False, env="ENABLE_DEBUG_ENDPOINTS")
    
    @validator("enable_mock_adapters")
    def validate_mock_in_production(cls, v, values):
        """Prevent mock adapters in production."""
        if v and values.get("environment") == Environment.PRODUCTION:
            raise ValueError("Mock adapters cannot be enabled in production")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()