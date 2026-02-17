"""
Database Configuration for Globe News
Includes admin approval fields for AdSense compliance
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from typing import Generator

logger = logging.getLogger(__name__)

# Use volume path for persistent storage - THIS IS THE KEY FIX
DB_PATH = os.environ.get('DB_PATH', '/app/data/globe_news.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create tables if they don't exist."""
    try:
        # Import models here to avoid circular imports
        from app.minimal_models import Base as ModelsBase
        ModelsBase.metadata.create_all(bind=engine)
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
