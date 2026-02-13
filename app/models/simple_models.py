"""
Simplified models for SQLite compatibility.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
import json

from app.database import Base


class SimpleNewsArticle(Base):
    """Simplified NewsArticle model for SQLite compatibility."""
    __tablename__ = "news_articles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(500), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    full_summary = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=False, unique=True, index=True)
    source_name = Column(String(200), nullable=False, index=True)
    source_domain = Column(String(200), nullable=False, index=True)
    image_url = Column(String(1000), nullable=True)
    main_category = Column(String(50), nullable=False, default="general", index=True)
    subcategories = Column(Text, nullable=True)  # Store as JSON string
    tags = Column(Text, nullable=True)  # Store as JSON string
    country = Column(String(100), nullable=True, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    language = Column(String(10), nullable=False, default="en", index=True)
    published_at = Column(DateTime, nullable=False, index=True)
    fetched_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    credibility_score = Column(Float, default=0.5)
    word_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)
    is_trending = Column(Boolean, default=False, index=True)
    is_breaking = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    save_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<NewsArticle {self.id}: {self.title[:50]}...>"
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        try:
            subcategories = json.loads(self.subcategories) if self.subcategories else []
        except:
            subcategories = []
            
        try:
            tags = json.loads(self.tags) if self.tags else []
        except:
            tags = []
        
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "full_summary": self.full_summary,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "source_domain": self.source_domain,
            "image_url": self.image_url,
            "main_category": self.main_category,
            "subcategories": subcategories,
            "tags": tags,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "language": self.language,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "credibility_score": self.credibility_score,
            "word_count": self.word_count,
            "reading_time_minutes": self.reading_time_minutes,
            "is_trending": self.is_trending,
            "is_breaking": self.is_breaking,
            "is_featured": self.is_featured,
            "view_count": self.view_count,
            "share_count": self.share_count,
        }


class SimpleNewsSource(Base):
    """Simplified NewsSource model for SQLite compatibility."""
    __tablename__ = "news_sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    short_name = Column(String(50), nullable=True, index=True)
    domain = Column(String(200), nullable=False, unique=True, index=True)
    base_url = Column(String(500), nullable=False)
    rss_url = Column(String(500), nullable=True)
    country = Column(String(100), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    primary_language = Column(String(10), nullable=False, default="en", index=True)
    source_type = Column(String(20), nullable=False, default="newspaper", index=True)
    categories = Column(Text, nullable=True)  # Store as JSON string
    political_bias = Column(String(20), nullable=True, index=True)
    credibility_score = Column(Float, default=0.5, index=True)
    trust_level = Column(String(20), nullable=True)
    logo_url = Column(String(500), nullable=True)
    color_primary = Column(String(7), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    article_count = Column(Integer, default=0, index=True)
    global_rank = Column(Integer, nullable=True, index=True)
    last_fetched = Column(DateTime, nullable=True, index=True)
    success_rate = Column(Float, default=0.0)
    twitter_handle = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<NewsSource {self.id}: {self.name} ({self.country_code})>"
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        try:
            categories = json.loads(self.categories) if self.categories else []
        except:
            categories = []
        
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "domain": self.domain,
            "country": self.country,
            "country_code": self.country_code,
            "primary_language": self.primary_language,
            "source_type": self.source_type,
            "categories": categories,
            "political_bias": self.political_bias,
            "credibility_score": self.credibility_score,
            "trust_level": self.trust_level,
            "logo_url": self.logo_url,
            "color_primary": self.color_primary,
            "is_active": self.is_active,
            "article_count": self.article_count,
            "global_rank": self.global_rank,
            "last_fetched": self.last_fetched.isoformat() if self.last_fetched else None,
            "success_rate": self.success_rate,
            "twitter_handle": self.twitter_handle,
        }


class SimpleCategory(Base):
    """Simplified Category model for SQLite compatibility."""
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    color = Column(String(7), nullable=False, default="#3498db")
    icon = Column(String(100), nullable=True)
    emoji = Column(String(10), nullable=True)
    article_count = Column(Integer, default=0, index=True)
    article_count_24h = Column(Integer, default=0)
    trending_score = Column(Float, default=0.0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    show_in_nav = Column(Boolean, default=True)
    show_on_homepage = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0, index=True)
    
    def __repr__(self):
        return f"<Category {self.slug}: {self.name}>"
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "display_name": self.display_name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "emoji": self.emoji,
            "article_count": self.article_count,
            "article_count_24h": self.article_count_24h,
            "trending_score": self.trending_score,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "show_in_nav": self.show_in_nav,
            "show_on_homepage": self.show_on_homepage,
            "sort_order": self.sort_order,
        }