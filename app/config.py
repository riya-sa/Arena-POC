"""
Application configuration management.
File: app/config.py

Environment-aware configuration using Pydantic v2 BaseSettings.
Loads from .env files and environment variables.
"""

from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings
from enum import Enum
from typing import List, Optional


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ========================================================================
    # Application
    # ========================================================================
    
    app_name: str = "C/AI Arena Optimization"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    
    # ========================================================================
    # Database Configuration
    # ========================================================================
    
    database_url: str = "postgresql+asyncpg://localhost/arena_dev"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False
    
    # ========================================================================
    # Authentication & Security
    # ========================================================================
    
    auth_enabled: bool = True
    oidc_issuer: Optional[str] = None
    oidc_audience: Optional[str] = None
    jwt_algorithm: str = "RS256"
    
    # ========================================================================
    # API Configuration
    # ========================================================================
    
    api_title: str = "C/AI Arena API"
    api_version: str = "v1"
    cors_origins: List[str] = ["*"]
    enable_debug_endpoints: bool = False
    
    # ========================================================================
    # Model Adapters & Candidates
    # ========================================================================
    
    adapter_type: str = "mock"  # openai, anthropic, local, mock
    adapter_config: dict = {}
    enable_mock_adapters: bool = True
    
    # ========================================================================
    # Queue Configuration
    # ========================================================================
    
    queue_type: str = "memory"  # database, memory (dev only)
    queue_polling_interval_ms: int = 1000
    queue_max_retries: int = 3
    queue_dlq_enabled: bool = True
    
    # ========================================================================
    # Evaluators
    # ========================================================================
    
    java_evaluator_enabled: bool = True
    java_home: Optional[str] = None
    sandbox_enabled: bool = True
    
    # ========================================================================
    # Observability & Logging
    # ========================================================================
    
    log_level: str = "DEBUG"
    log_format: str = "text"  # json (prod) or text (dev)
    
    opentelemetry_enabled: bool = False
    otel_exporter_otlp_endpoint: Optional[str] = None
    
    # ========================================================================
    # Secrets & External Services
    # ========================================================================
    
    secret_manager_type: str = "env"  # env, vault, aws_secrets
    secrets_refresh_interval_seconds: int = 300
    
    # API Keys (loaded from secrets manager in production)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # ========================================================================
    # Feature Flags
    # ========================================================================
    
    enable_experimental_features: bool = False
    
    # ========================================================================
    # Validators
    # ========================================================================
    
    @field_validator("enable_mock_adapters")
    @classmethod
    def validate_mock_in_production(cls, v: bool, info) -> bool:
        """
        Prevent mock adapters in production.
        
        Args:
            v: enable_mock_adapters value
            info: ValidationInfo with other field values
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If mock enabled in production
        """
        environment = info.data.get("environment")
        
        if v and environment == Environment.PRODUCTION:
            raise ValueError(
                "Mock adapters cannot be enabled in production environment. "
                "Set ENABLE_MOCK_ADAPTERS=false or switch to production API keys."
            )
        
        return v
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is known."""
        if v not in ["json", "text"]:
            raise ValueError(f"log_format must be 'json' or 'text', got {v}")
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v or len(v) < 5:
            raise ValueError("database_url is required and must be valid connection string")
        
        # Ensure PostgreSQL for async support
        if not ("postgresql" in v or "asyncpg" in v):
            raise ValueError(
                "Only PostgreSQL is supported. "
                "Use postgresql+asyncpg:// connection string. "
                f"Got: {v[:30]}..."
            )
        
        return v
    
    @field_validator("queue_type")
    @classmethod
    def validate_queue_type(cls, v: str, info) -> str:
        """Validate queue type."""
        if v not in ["database", "memory"]:
            raise ValueError(f"queue_type must be 'database' or 'memory', got {v}")
        
        # Memory queue only in development
        environment = info.data.get("environment")
        if v == "memory" and environment == Environment.PRODUCTION:
            raise ValueError(
                "Memory queue cannot be used in production. "
                "Use database queue for durability."
            )
        
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_production_config(cls, v: Environment, info) -> Environment:
        """
        Validate that production environment has required settings.
        """
        if v == Environment.PRODUCTION:
            log_format = info.data.get("log_format")
            auth_enabled = info.data.get("auth_enabled")
            queue_type = info.data.get("queue_type")
            
            if log_format != "json":
                raise ValueError(
                    f"Production environment requires log_format='json', got '{log_format}'. "
                    "Set LOG_FORMAT=json"
                )
            
            if not auth_enabled:
                raise ValueError(
                    "Production environment requires auth_enabled=true. "
                    "Set AUTH_ENABLED=true"
                )
            
            if queue_type == "memory":
                raise ValueError(
                    "Production environment requires queue_type='database'. "
                    "Set QUEUE_TYPE=database"
                )
        
        return v


# ============================================================================
# Global Settings Instance
# ============================================================================

try:
    settings = Settings()
    
    # Print startup info
    print(f"✅ Configuration loaded")
    print(f"   Environment: {settings.environment.value}")
    print(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url[:40]}")
    print(f"   Logging: {settings.log_format} ({settings.log_level})")
    print(f"   Adapters: {settings.adapter_type}" + (" (mock - development)" if settings.enable_mock_adapters else ""))
    
except Exception as e:
    print(f"❌ Configuration error: {str(e)}")
    raise