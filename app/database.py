"""
Database Configuration for Globe News
Includes admin approval fields for AdSense compliance
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELS ====================

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="category_rel")

class NewsSource(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True)
    reliability_score = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="source_rel")

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    
    # AI-generated summaries
    ai_summary_1 = Column(Text, nullable=True)
    ai_summary_2 = Column(Text, nullable=True)
    ai_summary_3 = Column(Text, nullable=True)
    ai_summary_4 = Column(Text, nullable=True)
    ai_summary_5 = Column(Text, nullable=True)
    ai_summary_6 = Column(Text, nullable=True)
    ai_summary_generated = Column(Boolean, default=False)
    ai_summary_generated_at = Column(DateTime, nullable=True)
    
    full_content = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False)
    image_url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=True)
    author = Column(String(200), nullable=True)
    
    # Foreign keys
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Additional fields
    country = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True)
    is_trending = Column(Boolean, default=False)
    is_breaking = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ADMIN APPROVAL FIELDS - For AdSense compliance
    is_approved = Column(Boolean, default=False)      # Article must be approved to show on site
    is_rejected = Column(Boolean, default=False)       # Rejected articles stay hidden
    is_edited = Column(Boolean, default=False)         # Whether article was manually edited
    
    approved_at = Column(DateTime, nullable=True)       # When approved
    approved_by = Column(String(100), nullable=True)    # Admin username who approved
    rejected_at = Column(DateTime, nullable=True)       # When rejected
    rejected_by = Column(String(100), nullable=True)    # Admin username who rejected
    edited_at = Column(DateTime, nullable=True)         # Last edit time
    edited_by = Column(String(100), nullable=True)      # Admin username who last edited
    
    editor_notes = Column(Text, nullable=True)          # Internal notes for editors
    
    # Relationships
    source_rel = relationship("NewsSource", back_populates="articles")
    category_rel = relationship("Category", back_populates="articles")
    
    @property
    def is_public(self):
        """Check if article should be visible to public"""
        return self.is_approved and not self.is_rejected

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
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create default categories if they don't exist
        db = SessionLocal()
        try:
            default_categories = [
                ("World", "International news and global events"),
                ("Technology", "Tech news, gadgets, and innovations"),
                ("Business", "Business, finance, and economy"),
                ("Science", "Scientific discoveries and research"),
                ("Entertainment", "Movies, music, and celebrity news"),
                ("Sports", "Sports news and updates"),
                ("Health", "Health, wellness, and medicine"),
                ("Politics", "Political news and analysis"),
                ("General", "General news and current events")
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
