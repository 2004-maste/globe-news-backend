"""
Minimal Models for Globe News
SQLAlchemy models with all necessary fields including admin approval
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="category_rel")
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Source(Base):
    __tablename__ = "sources"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reliability_score: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fetch_frequency: Mapped[int] = mapped_column(Integer, default=30)  # minutes
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="source_rel")
    
    def __repr__(self):
        return f"<Source {self.name}>"


class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # RSS description/summary
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Alias for summary

    # Content fields
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # RSS content/snippet
    full_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Extracted full article
    preview_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Enhanced preview/analysis
    
    # Article metadata
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    url_to_image: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # Alias for image_url
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Foreign keys
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Additional fields
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default='en')
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Content metrics
    has_full_content: Mapped[bool] = mapped_column(Boolean, default=False)
    content_length: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ========== ADMIN APPROVAL FIELDS (for AdSense compliance) ==========
    # Approval status
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)  # Whether article is approved for public
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)  # Whether article was rejected
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)    # Whether article was manually edited
    
    # Approval timestamps and metadata
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # When approved
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # Who approved
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # When rejected
    rejected_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # Who rejected
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)     # Last edit time
    edited_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)       # Who last edited
    
    # Editorial notes
    editor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)           # Internal notes for editors
    
    # Relationships
    source_rel: Mapped[Optional["Source"]] = relationship("Source", back_populates="articles")
    category_rel: Mapped[Optional["Category"]] = relationship("Category", back_populates="articles")
    
    @property
    def is_public(self):
        """Check if article should be visible to public"""
        return self.is_approved and not self.is_rejected
    
    @property
    def category(self):
        """For backward compatibility"""
        return self.category_rel
    
    @property
    def source(self):
        """For backward compatibility"""
        return self.source_rel
    
    def __repr__(self):
        return f"<Article {self.title[:50]}...>"


# For backward compatibility and easier imports
NewsArticle = Article
NewsSource = Source
Category = Category

__all__ = [
    'Base',
    'Article',
    'Category',
    'Source',
    'NewsArticle',
    'NewsSource'
]
