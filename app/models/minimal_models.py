"""
Minimal Models for Globe News - MATCHING OLD DATABASE SCHEMA (2480 articles)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
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
    
    # Fixed relationship to match the back_populates in Article
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Core content fields
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # RSS summary
    
    # ===== NEW FIELD FOR HUMAN SUMMARIES =====
    human_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Editor-written summary
    # ==========================================
    
    # Article metadata
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    url_to_image: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Foreign key
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Source info
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Language & status
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default='en')
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance tracking fields
    read_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fetch_count: Mapped[int] = mapped_column(Integer, default=0)
    last_fetched: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    content_fetched: Mapped[bool] = mapped_column(Boolean, default=False)
    fetch_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_fetch_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # ========== ADMIN APPROVAL FIELDS ==========
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    edited_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    editor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships - Fixed to match Category's back_populates
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="articles")
    
    @property
    def image_url(self):
        return self.url_to_image or self.thumbnail_url
    
    @property
    def is_public(self):
        return self.is_approved and not self.is_rejected
    
    @property
    def category_name(self):
        return self.category.name if self.category else None
    
    @property
    def display_summary(self):
        """Returns human summary if available, otherwise falls back to preview_content or summary"""
        if self.human_summary:
            return self.human_summary
        elif self.preview_content:
            return self.preview_content
        else:
            return self.summary
    
    def __repr__(self):
        return f"<Article {self.title[:50]}...>"


# For backward compatibility
NewsArticle = Article

__all__ = [
    'Base',
    'Article',
    'Category',
    'NewsArticle'
]


class Movie(Base):
    """Movie and TV Show model"""
    __tablename__ = "movies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # TMDB original ID
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'movie' or 'tv'
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Media URLs
    poster_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    backdrop_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Details
    release_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_air_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    runtime: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    number_of_seasons: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    number_of_episodes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Ratings
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    popularity: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Metadata
    language: Mapped[str] = mapped_column(String(10), default='en')
    genres: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    cast: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    director: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    creator: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    networks: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    production_companies: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # Streaming Info
    streaming_info: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Content
    preview_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Admin flags
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    similar_movies: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    def __repr__(self):
        return f"<Movie {self.title} ({self.type})>"
