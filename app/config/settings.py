# """
# Week 11: Production Configuration Settings

# Environment-based configuration with Pydantic validation.
# Replace app/config.py with this file.

# Usage:
#     from app.config.settings import settings
#     db_url = settings.database_url
#     debug = settings.debug
# """

# from pydantic_settings import BaseSettings
# from typing import Literal
# import os
# from pathlib import Path

# class Settings(BaseSettings):
#     """Production-grade application settings with environment validation"""
    
#     # ============================================================================
#     # ENVIRONMENT
#     # ============================================================================
#     environment: Literal["development", "staging", "production","test"] = os.getenv(
#         "ENVIRONMENT", "development"
#     )
#     debug: bool = False  # Explicitly set, don't infer from environment
    
#     # ============================================================================
#     # API CONFIGURATION
#     # ============================================================================
#     api_title: str = "C/AI Arena Optimization"
#     api_version: str = "1.0.0"
#     api_host: str = "0.0.0.0"
#     api_port: int = int(os.getenv("PORT", "8000"))
#     api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
#     # ============================================================================
#     # DATABASE
#     # ============================================================================
#     database_url: str = os.getenv(
#         "DATABASE_URL",
#         "postgresql://arena_user:arena_pass@localhost:5432/arena_poc"
#     )
#     database_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
#     database_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
#     database_pool_pre_ping: bool = True  # Verify connections before using
#     database_echo: bool = False  # Log SQL queries (set to True for debug)
    
#     # ============================================================================
#     # SECURITY
#     # ============================================================================
#     secret_key: str = os.getenv(
#         "SECRET_KEY", "change-me-in-production-with-random-string"
#     )
#     cors_origins: list[str] = [
#         "http://localhost:3000",
#         "http://localhost:5173",  # Vite default
#         "http://localhost:8000",  # API itself
#     ]
#     allowed_hosts: list[str] = [
#         "localhost",
#         "127.0.0.1",
#         os.getenv("ALLOWED_HOST", "localhost"),
#     ]
    
#     # ============================================================================
#     # WORKERS
#     # ============================================================================
#     worker_timeout_seconds: int = int(os.getenv("WORKER_TIMEOUT", "30"))
#     worker_max_retries: int = int(os.getenv("WORKER_MAX_RETRIES", "3"))
#     worker_backoff_multiplier: float = 2.0
#     worker_visibility_timeout_seconds: int = 60
    
#     # ============================================================================
#     # FEATURES & FEATURE FLAGS
#     # ============================================================================
#     # CRITICAL: Mock adapters must be disabled in production
#     mock_adapters_enabled: bool = os.getenv("ENVIRONMENT", "development") != "production"
    
#     # Feature flags
#     enable_statistics_ranking: bool = True
#     enable_blind_arena: bool = True
#     enable_multi_language_support: bool = False  # Roadmap item
    
#     # ============================================================================
#     # OBSERVABILITY
#     # ============================================================================
#     log_level: str = os.getenv("LOG_LEVEL", "INFO" if environment == "production" else "DEBUG")
#     log_format: str = "json" if environment == "production" else "plain"
#     trace_sample_rate: float = float(os.getenv("TRACE_SAMPLE_RATE", "0.1" if environment == "production" else "1.0"))
    
#     # ============================================================================
#     # EXECUTION LIMITS
#     # ============================================================================
#     max_input_tokens: int = 4000  # Max tokens in prompt
#     max_output_tokens: int = 2000  # Max tokens in response
#     max_java_compilation_time_seconds: int = 10
#     max_java_execution_time_seconds: int = 5
#     max_java_output_size_bytes: int = 1024 * 1024  # 1MB
    
#     # ============================================================================
#     # COST & BUDGET
#     # ============================================================================
#     max_cost_per_task_cents: int = 100  # $1 limit per task
#     max_cost_per_experiment_dollars: float = 1000.0
    
#     # ============================================================================
#     # PAGINATION
#     # ============================================================================
#     default_page_size: int = 20
#     max_page_size: int = 100
    
#     class Config:
#         # Load from .env file if it exists
#         env_file = ".env"
#         case_sensitive = False
#         # Allow extra fields (future-proofing)
#         extra = "allow"


# # ============================================================================
# # INITIALIZATION & VALIDATION
# # ============================================================================

# settings = Settings()

# # Validate production constraints
# if settings.environment == "production":
#     print("\n" + "="*70)
#     print("PRODUCTION ENVIRONMENT DETECTED - Running security checks...")
#     print("="*70 + "\n")
    
#     # Check 1: Debug mode disabled
#     if settings.debug:
#         raise ValueError("❌ Debug mode CANNOT be enabled in production")
#     print("✅ Debug mode is disabled")
    
#     # Check 2: Mock adapters disabled
#     if settings.mock_adapters_enabled:
#         raise ValueError("❌ Mock adapters CANNOT be enabled in production")
#     print("✅ Mock adapters are disabled")
    
#     # Check 3: Secret key changed
#     if settings.secret_key == "change-me-in-production-with-random-string":
#         raise ValueError("❌ SECRET_KEY must be set to a secure random string in production")
#     print("✅ SECRET_KEY is configured")
    
#     # Check 4: Database URL configured
#     if "localhost" in settings.database_url:
#         raise ValueError("❌ Database must use managed service in production, not localhost")
#     print("✅ Database is configured for production")
    
#     # Check 5: API base URL set
#     if "localhost" in settings.api_base_url:
#         raise ValueError("❌ API_BASE_URL must be production domain, not localhost")
#     print("✅ API base URL is configured\n")
#     print("="*70)
#     print("All production security checks passed ✅\n")
#     print("="*70 + "\n")


# # ============================================================================
# # ENVIRONMENT-SPECIFIC DEFAULTS
# # ============================================================================

# if settings.environment == "development":
#     settings.database_echo = True  # Log SQL in development
#     settings.log_level = "DEBUG"
# elif settings.environment == "staging":
#     settings.log_level = "INFO"
#     settings.trace_sample_rate = 0.5  # 50% sampling


# # ============================================================================
# # USAGE EXAMPLES
# # ============================================================================

# """
# # In your application code:

# from app.config.settings import settings

# # Database connection
# DATABASE_URL = settings.database_url
# POOL_SIZE = settings.database_pool_size

# # API configuration
# API_TITLE = settings.api_title
# API_VERSION = settings.api_version

# # Features
# if settings.mock_adapters_enabled:
#     adapter = MockAdapter()  # OK in dev/test
# else:
#     adapter = RealAdapter()  # Production only

# # Logging
# import logging
# logger = logging.getLogger(__name__)
# logger.setLevel(settings.log_level)

# # Execution limits
# if prompt_tokens > settings.max_input_tokens:
#     raise ValueError(f"Input too large: {prompt_tokens} > {settings.max_input_tokens}")
# """


# # ============================================================================
# # .ENV FILE EXAMPLE
# # ============================================================================

# """
# Create .env file in project root:

# # Environment
# ENVIRONMENT=production
# DEBUG=false
# LOG_LEVEL=INFO

# # Database (RDS, CloudSQL, or managed PostgreSQL)
# DATABASE_URL=postgresql://user:password@prod-db.rds.amazonaws.com:5432/arena_prod
# DB_POOL_SIZE=20

# # API
# API_BASE_URL=https://arena.yourdomain.com
# PORT=8000

# # Security
# SECRET_KEY=your-random-secure-key-here-generate-with-secrets.token_hex(32)
# ALLOWED_HOST=arena.yourdomain.com

# # Workers
# WORKER_TIMEOUT=30
# WORKER_MAX_RETRIES=3

# # Observability
# TRACE_SAMPLE_RATE=0.1

# # Feature flags
# MOCK_ADAPTERS_ENABLED=false
# """

# # """
# app/config/settings.py

# Copy this EXACTLY to: app/config/settings.py
# NO EDITING NEEDED - This handles all environments correctly
# """

# from pydantic_settings import BaseSettings
# from typing import Literal
# import os


# class Settings(BaseSettings):
#     """Production-grade application settings"""
    
#     environment: Literal["development", "staging", "production", "test"] = os.getenv(
#         "ENVIRONMENT", "development"
#     )
#     debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
#     # API
#     api_title: str = "C/AI Arena Optimization"
#     api_version: str = "1.0.0"
#     api_host: str = "0.0.0.0"
#     api_port: int = int(os.getenv("PORT", "8000"))
#     api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
#     # Database (Always PostgreSQL - no in-memory)
#     database_url: str = os.getenv(
#         "DATABASE_URL",
#         "postgresql://arena_user:arena_pass@localhost:5432/arena_poc"
#     )
#     database_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
#     database_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
#     database_pool_pre_ping: bool = True
#     database_echo: bool = False
    
#     # Security
#     secret_key: str = os.getenv("SECRET_KEY", "dev-key")
#     cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
#     allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    
#     # Workers
#     worker_timeout_seconds: int = 30
#     worker_max_retries: int = 3
#     worker_backoff_multiplier: float = 2.0
    
#     # Features
#     mock_adapters_enabled: bool = os.getenv("ENVIRONMENT", "development") != "production"
#     enable_statistics_ranking: bool = True
#     enable_blind_arena: bool = True
#     enable_multi_language_support: bool = False
    
#     # Observability (set based on environment below)
#     log_level: str = "DEBUG"
#     log_format: str = "plain"
#     trace_sample_rate: float = 1.0
    
#     # Execution Limits
#     max_input_tokens: int = 4000
#     max_output_tokens: int = 2000
#     max_java_compilation_time_seconds: int = 10
#     max_java_execution_time_seconds: int = 5
#     max_java_output_size_bytes: int = 1024 * 1024
    
#     # Pagination
#     default_page_size: int = 20
#     max_page_size: int = 100
    
#     class Config:
#         env_file = ".env"
#         case_sensitive = False
#         extra = "allow"


# # Create settings instance
# settings = Settings()

# # Set environment-specific values AFTER settings is created
# if settings.environment == "production":
#     settings.log_level = "INFO"
#     settings.log_format = "json"
#     settings.trace_sample_rate = 0.1
#     settings.database_echo = False
    
#     # Validate production
#     if settings.debug:
#         raise ValueError("Debug cannot be True in production")
#     if settings.mock_adapters_enabled:
#         raise ValueError("Mock adapters cannot be enabled in production")

# elif settings.environment == "staging":
#     settings.log_level = "INFO"
#     settings.trace_sample_rate = 0.5
#     settings.database_echo = False

# elif settings.environment == "development":
#     settings.log_level = "DEBUG"
#     settings.trace_sample_rate = 1.0
#     settings.database_echo = True
#     settings.debug = True

# elif settings.environment == "test":
#     settings.log_level = "DEBUG"
#     settings.trace_sample_rate = 1.0
#     settings.database_echo = False
#     settings.debug = False



# """
# Week 11: Production Configuration Settings

# Environment-based configuration with Pydantic validation.
# Replace app/config.py with this file.

# Usage:
#     from app.config.settings import settings
#     db_url = settings.database_url
#     debug = settings.debug
# """

# from pydantic import field_validator, ValidationInfo
# from pydantic_settings import BaseSettings
# from typing import Literal, Any
# import os
# from pathlib import Path

# class Settings(BaseSettings):
#     """Production-grade application settings with environment validation"""
    
#     # ============================================================================
#     # ENVIRONMENT
#     # ============================================================================
#     environment: Literal["development", "staging", "production","test"] = os.getenv(
#         "ENVIRONMENT", "development"
#     )
#     debug: bool = False  # Explicitly set, don't infer from environment
    
#     # ============================================================================
#     # API CONFIGURATION
#     # ============================================================================
#     api_title: str = "C/AI Arena Optimization"
#     api_version: str = "1.0.0"
#     api_host: str = "0.0.0.0"
#     api_port: int = int(os.getenv("PORT", "8000"))
#     api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
#     # ============================================================================
#     # DATABASE
#     # ============================================================================
#     database_url: str = os.getenv(
#         "DATABASE_URL",
#         "postgresql://arena_user:arena_pass@localhost:5432/arena_poc"
#     )
#     database_pool_size: int | None = int(os.getenv("DB_POOL_SIZE", "20"))
#     database_max_overflow: int | None = int(os.getenv("DB_MAX_OVERFLOW", "10"))
#     database_pool_pre_ping: bool = True  # Verify connections before using
#     database_echo: bool = False  # Log SQL queries (set to True for debug)
    
#     # ============================================================================
#     # DYNAMIC FIELD VALIDATORS FOR SQLITE COMPATIBILITY (BYPASSES MAX_OVERFLOW ERRORS)
#     # ============================================================================
#     @field_validator('database_pool_size', 'database_max_overflow', mode='before')
#     @classmethod
#     def clear_pooling_for_sqlite(cls, value: Any, info: ValidationInfo) -> Any:
#         """Strips out pooling variables if conftest.py forces an in-memory SQLite URL"""
#         # Access the database_url field from the current initialization context
#         db_url = info.data.get("database_url", "")
#         if "sqlite" in db_url or (os.getenv("DATABASE_URL") and "sqlite" in os.getenv("DATABASE_URL")):
#             return None
#         return value

#     # ============================================================================
#     # SECURITY
#     # ============================================================================
#     secret_key: str = os.getenv(
#         "SECRET_KEY", "change-me-in-production-with-random-string"
#     )
#     cors_origins: list[str] = [
#         "http://localhost:3000",
#         "http://localhost:5173",  # Vite default
#         "http://localhost:8000",  # API itself
#     ]
#     allowed_hosts: list[str] = [
#         "localhost",
#         "127.0.0.1",
#         os.getenv("ALLOWED_HOST", "localhost"),
#     ]
    
#     # ============================================================================
#     # WORKERS
#     # ============================================================================
#     worker_timeout_seconds: int = int(os.getenv("WORKER_TIMEOUT", "30"))
#     worker_max_retries: int = int(os.getenv("WORKER_MAX_RETRIES", "3"))
#     worker_backoff_multiplier: float = 2.0
#     worker_visibility_timeout_seconds: int = 60
    
#     # ============================================================================
#     # FEATURES & FEATURE FLAGS
#     # ============================================================================
#     # CRITICAL: Mock adapters must be disabled in production
#     mock_adapters_enabled: bool = os.getenv("ENVIRONMENT", "development") != "production"
    
#     # Feature flags
#     enable_statistics_ranking: bool = True
#     enable_blind_arena: bool = True
#     enable_multi_language_support: bool = False  # Roadmap item
    
#     # ============================================================================
#     # OBSERVABILITY
#     # ============================================================================
#     log_level: str = os.getenv("LOG_LEVEL", "INFO" if environment == "production" else "DEBUG")
#     log_format: str = "json" if environment == "production" else "plain"
#     trace_sample_rate: float = 0.1 # Base default initialized to prevent parsing sequence breaks
    
#     # ============================================================================
#     # EXECUTION LIMITS
#     # ============================================================================
#     max_input_tokens: int = 4000  # Max tokens in prompt
#     max_output_tokens: int = 2000  # Max tokens in response
#     max_java_compilation_time_seconds: int = 10
#     max_java_execution_time_seconds: int = 5
#     max_java_output_size_bytes: int = 1024 * 1024  # 1MB
    
#     # ============================================================================
#     # COST & BUDGET
#     # ============================================================================
#     max_cost_per_task_cents: int = 100  # $1 limit per task
#     max_cost_per_experiment_dollars: float = 1000.0
    
#     # ============================================================================
#     # PAGINATION
#     # ============================================================================
#     default_page_size: int = 20
#     max_page_size: int = 100
    
#     class Config:
#         # Load from .env file if it exists
#         env_file = ".env"
#         case_sensitive = False
#         # Allow extra fields (future-proofing)
#         extra = "allow"


# # ============================================================================
# # INITIALIZATION & VALIDATION
# # ============================================================================

# settings = Settings()

# # Post-processing assignment mapping for Trace Rate calculations
# settings.trace_sample_rate = float(os.getenv("TRACE_SAMPLE_RATE", "0.1" if settings.environment == "production" else "1.0"))

# # Validate production constraints
# if settings.environment == "production":
#     print("\n" + "="*70)
#     print("PRODUCTION ENVIRONMENT DETECTED - Running security checks...")
#     print("="*70 + "\n")
    
#     if settings.debug:
#         raise ValueError("❌ Debug mode CANNOT be enabled in production")
#     print("✅ Debug mode is disabled")
    
#     if settings.mock_adapters_enabled:
#         raise ValueError("❌ Mock adapters CANNOT be enabled in production")
#     print("✅ Mock adapters are disabled")
    
#     if settings.secret_key == "change-me-in-production-with-random-string":
#         raise ValueError("❌ SECRET_KEY must be set to a secure random string in production")
#     print("✅ SECRET_KEY is configured")
    
#     if "localhost" in settings.database_url:
#         raise ValueError("❌ Database must use managed service in production, not localhost")
#     print("✅ Database is configured for production")
    
#     if "localhost" in settings.api_base_url:
#         raise ValueError("❌ API_BASE_URL must be production domain, not localhost")
#     print("✅ API base URL is configured\n")
#     print("="*70)
#     print("All production security checks passed ✅\n")
#     print("="*70 + "\n")


# # ============================================================================
# # ENVIRONMENT-SPECIFIC DEFAULTS
# # ============================================================================

# if settings.environment == "development":
#     settings.database_echo = True  # Log SQL in development
#     settings.log_level = "DEBUG"
# elif settings.environment == "staging":
#     settings.log_level = "INFO"
#     settings.trace_sample_rate = 0.5  # 50% sampling


"""
app/config/settings.py

Copy this EXACTLY to: app/config/settings.py
NO EDITING NEEDED - This handles all environments correctly
"""

from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    """Production-grade application settings"""
    
    environment: Literal["development", "staging", "production", "test"] = os.getenv(
        "ENVIRONMENT", "development"
    )
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API
    api_title: str = "C/AI Arena Optimization"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Database (Always PostgreSQL - no in-memory)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://arena_user:arena_pass@localhost:5432/arena_poc"
    )
    database_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    database_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    database_pool_pre_ping: bool = True
    database_echo: bool = False
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-key")
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    
    # Workers
    worker_timeout_seconds: int = 30
    worker_max_retries: int = 3
    worker_backoff_multiplier: float = 2.0
    
    # Features
    mock_adapters_enabled: bool = os.getenv("ENVIRONMENT", "development") != "production"
    enable_statistics_ranking: bool = True
    enable_blind_arena: bool = True
    enable_multi_language_support: bool = False
    
    # Observability (set based on environment below)
    log_level: str = "DEBUG"
    log_format: str = "plain"
    trace_sample_rate: float = 1.0
    
    # Execution Limits
    max_input_tokens: int = 4000
    max_output_tokens: int = 2000
    max_java_compilation_time_seconds: int = 10
    max_java_execution_time_seconds: int = 5
    max_java_output_size_bytes: int = 1024 * 1024
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


# Create settings instance
settings = Settings()

# Set environment-specific values AFTER settings is created
if settings.environment == "production":
    settings.log_level = "INFO"
    settings.log_format = "json"
    settings.trace_sample_rate = 0.1
    settings.database_echo = False
    
    # Validate production
    if settings.debug:
        raise ValueError("Debug cannot be True in production")
    if settings.mock_adapters_enabled:
        raise ValueError("Mock adapters cannot be enabled in production")

elif settings.environment == "staging":
    settings.log_level = "INFO"
    settings.trace_sample_rate = 0.5
    settings.database_echo = False

elif settings.environment == "development":
    settings.log_level = "DEBUG"
    settings.trace_sample_rate = 1.0
    settings.database_echo = True
    settings.debug = True

elif settings.environment == "test":
    settings.log_level = "DEBUG"
    settings.trace_sample_rate = 1.0
    settings.database_echo = False
    settings.debug = False
