"""
Pydantic schemas for news articles.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
import uuid


class ArticleBase(BaseModel):
    """Base schema for articles."""
    title: str = Field(..., max_length=500, description="Article title")
    summary: Optional[str] = Field(None, description="Short summary")
    source_url: HttpUrl = Field(..., description="Original article URL")
    source_name: str = Field(..., max_length=200, description="Source name")
    source_domain: str = Field(..., max_length=200, description="Source domain")
    image_url: Optional[HttpUrl] = Field(None, description="Main image URL")
    main_category: str = Field("general", description="Main category")
    language: str = Field("en", description="Language code")


class ArticleCreate(ArticleBase):
    """Schema for creating articles."""
    original_content: Optional[str] = Field(None, description="Full article content")
    published_at: datetime = Field(..., description="Publication date")
    authors: Optional[List[str]] = Field(None, description="Article authors")
    keywords: Optional[List[str]] = Field(None, description="Keywords")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Global Climate Summit Reaches Historic Agreement",
                "summary": "World leaders agree on ambitious climate targets",
                "source_url": "https://example.com/news/climate-summit",
                "source_name": "Example News",
                "source_domain": "example.com",
                "image_url": "https://example.com/image.jpg",
                "main_category": "environment",
                "language": "en",
                "original_content": "Full article text here...",
                "published_at": "2024-01-15T10:30:00Z",
                "authors": ["John Doe", "Jane Smith"],
                "keywords": ["climate", "summit", "agreement"]
            }
        }


class ArticleUpdate(BaseModel):
    """Schema for updating articles."""
    title: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    full_summary: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    main_category: Optional[str] = None
    subcategories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    sentiment_label: Optional[str] = None
    is_trending: Optional[bool] = None
    is_breaking: Optional[bool] = None
    is_featured: Optional[bool] = None
    credibility_score: Optional[float] = Field(None, ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tags": ["climate", "politics", "environment"],
                "sentiment_score": 0.7,
                "sentiment_label": "positive",
                "is_trending": True
            }
        }


class ArticleResponse(ArticleBase):
    """Schema for article responses."""
    id: uuid.UUID
    clean_title: Optional[str]
    full_summary: Optional[str]
    subcategories: Optional[List[str]]
    tags: Optional[List[str]]
    topics: Optional[List[str]]
    country: Optional[str]
    country_code: Optional[str]
    region: Optional[str]
    detected_language: Optional[str]
    is_translated: bool
    published_at: datetime
    fetched_at: datetime
    updated_at: datetime
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    credibility_score: float
    word_count: Optional[int]
    reading_time_minutes: Optional[int]
    is_trending: bool
    is_breaking: bool
    is_featured: bool
    view_count: int
    share_count: int
    like_count: int
    save_count: int
    
    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Schema for paginated article lists."""
    items: List[ArticleResponse]
    total: int
    page: int
    size: int
    pages: int
    
    class Config:
        from_attributes = True


class ArticleFilter(BaseModel):
    """Schema for filtering articles."""
    category: Optional[str] = None
    categories: Optional[List[str]] = None
    country: Optional[str] = None
    countries: Optional[List[str]] = None
    language: Optional[str] = None
    languages: Optional[List[str]] = None
    source_id: Optional[uuid.UUID] = None
    source_name: Optional[str] = None
    source_domain: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_trending: Optional[bool] = None
    is_breaking: Optional[bool] = None
    is_featured: Optional[bool] = None
    min_credibility: Optional[float] = Field(None, ge=0, le=1)
    search: Optional[str] = None
    tags: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "technology",
                "country": "US",
                "date_from": "2024-01-01T00:00:00Z",
                "is_trending": True,
                "min_credibility": 0.7
            }
        }


class ArticleSummaryRequest(BaseModel):
    """Schema for requesting article summaries."""
    length: str = Field("medium", description="Summary length: short, medium, long, full")
    paragraphs: int = Field(6, ge=1, le=10, description="Number of paragraphs")
    include_key_points: bool = Field(True, description="Include key points")
    
    class Config:
        json_schema_extra = {
            "example": {
                "length": "medium",
                "paragraphs": 6,
                "include_key_points": True
            }
        }


class ArticleSummaryResponse(BaseModel):
    """Schema for article summary responses."""
    id: uuid.UUID
    title: str
    source_name: str
    summary: Optional[str]
    full_summary: Optional[str]
    paragraphs: Optional[List[str]]
    key_points: Optional[List[str]]
    reading_time_minutes: int
    sentiment_label: Optional[str]
    
    class Config:
        from_attributes = True