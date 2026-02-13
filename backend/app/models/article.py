"""
Database Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(500), unique=True, nullable=False)
    url_to_image = Column(String(500))
    published_at = Column(DateTime, nullable=False, index=True)
    content = Column(Text)
    summary = Column(Text)  # AI-generated summary
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    source = Column(String(200))
    author = Column(String(200))
    language = Column(String(10), default="en", index=True)
    is_breaking = Column(Boolean, default=False)
    is_fetched = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="articles")
    
    # Indexes
    __table_args__ = (
        Index('ix_articles_language_published', 'language', 'published_at'),
        Index('ix_articles_source_category', 'source', 'category_id'),
    )

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    articles = relationship("Article", back_populates="category")

class NewsSource(Base):
    __tablename__ = "news_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500))
    language = Column(String(10))
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())