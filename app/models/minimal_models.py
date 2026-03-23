"""
Minimal Models for Globe News - MATCHING OLD DATABASE SCHEMA (2480 articles)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
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
    
    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False)  # TMDB original ID
    type = Column(String(10), nullable=False)  # 'movie' or 'tv'
    title = Column(String(500), nullable=False)
    original_title = Column(String(500))
    overview = Column(Text)
    tagline = Column(String(500))
    
    # Media URLs
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))
    
    # Details
    release_date = Column(String(50))  # first_air_date for TV
    last_air_date = Column(String(50))  # for TV only
    runtime = Column(Integer)  # for movies
    number_of_seasons = Column(Integer)  # for TV
    number_of_episodes = Column(Integer)  # for TV
    
    # Ratings
    rating = Column(Float, default=0.0)
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0)
    
    # Metadata
    language = Column(String(10), default='en')
    genres = Column(JSON, default=list)  # List of genre names
    cast = Column(JSON, default=list)  # List of cast members
    director = Column(String(200))  # for movies
    creator = Column(String(200))  # for TV
    networks = Column(JSON, default=list)  # for TV
    production_companies = Column(JSON, default=list)
    
    # Streaming Info
    streaming_info = Column(JSON, default=dict)  # Where to watch
    
    # Smart Content Preview (your algorithm)
    preview_content = Column(Text)  # Generated by ContentAnalyzer
    
    # Human Summary (editor's pick)
    human_summary = Column(Text)
    
    # Admin flags
    is_approved = Column(Boolean, default=True)  # Auto-approved by default
    is_trending = Column(Boolean, default=False)  # Marked as trending
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    similar_movies = Column(JSON, default=list)  # Store similar movie IDs
    
    def __repr__(self):
        return f"<Movie {self.title} ({self.type})>"
