"""
app/infrastructure/database.py

Copy this file directly to: app/infrastructure/database.py
NO EDITING NEEDED
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.settings import settings

# Create base class for models
Base = declarative_base()

# Create engine
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=settings.database_pool_pre_ping,
    echo=settings.database_echo,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database (create all tables)"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")