"""
Database Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database."""
    try:
        # Import models here to ensure they are registered with SQLAlchemy
        from app.models.article import Article, Category, NewsSource
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create default categories if they don't exist
        db = SessionLocal()
        try:
            default_categories = [
                ("World", "International news"),
                ("Technology", "Tech news and innovations"),
                ("Business", "Business and economy"),
                ("Science", "Scientific discoveries"),
                ("Entertainment", "Movies, music, and arts"),
                ("Sports", "Sports news"),
                ("Health", "Health and medicine"),
                ("Politics", "Political news"),
                ("General", "General news")
            ]
            
            for name, description in default_categories:
                existing = db.query(Category).filter(Category.name == name).first()
                if not existing:
                    category = Category(name=name, description=description)
                    db.add(category)
            
            db.commit()
            logger.info("Database initialized with default categories")
            
        except Exception as e:
            logger.error(f"Error initializing categories: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise