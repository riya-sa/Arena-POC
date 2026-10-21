"""
Database configuration and setup.
File: app/database.py
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Base class for all models
Base = declarative_base()

# Global engine and session factory (initialized on app startup)
_engine = None
_async_session_maker = None


# async def init_db():
#     """
#     Initialize database engine and connection pool.
#     Call this in app startup event.
#     """
#     global _engine, _async_session_maker

#     database_url = settings.database_url

#     logger.info(
#         f"Initializing database: {database_url.split('@')[1] if '@' in database_url else database_url}"
#     )

#     # Create async engine
#     _engine = create_async_engine(
#         database_url,
#         echo=settings.database_echo,
#         pool_size=settings.database_pool_size,
#         max_overflow=settings.database_max_overflow,
#         pool_pre_ping=True,  # Verify connections before using
#         connect_args={"timeout": 30, "command_timeout": 30},
#     )

#     # Create session factory
#     _async_session_maker = async_sessionmaker(
#         _engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
#     )

#     # Create tables
#     async with _engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     logger.info("Database initialized successfully")

async def init_db():
    """Initialize database engine and connection pool."""
    global _engine, _async_session_maker
    
    database_url = settings.database_url
    
    try:
        logger.info(f"Initializing database: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        _engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
            connect_args={
                "timeout": 10,
                "command_timeout": 10
            }
        )
        
        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        # Try to connect (won't block, just creates pool)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database initialized successfully")
    
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {str(e)}")
        if settings.environment.value == "production":
            raise
        # Development: continue without database
        logger.info("Continuing without database (development mode)")
        _engine = None
        _async_session_maker = None


async def close_db():
    """
    Close database engine and connections.
    Call this in app shutdown event.
    """
    global _engine

    if _engine:
        await _engine.dispose()
        logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session.

    Usage:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() on app startup.")

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_session() -> AsyncSession:
    """
    Get database session outside FastAPI dependency injection.

    Usage in services/workers:
        session = await get_session()
        try:
            # Use session
        finally:
            await session.close()
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() on app startup.")

    return _async_session_maker()
