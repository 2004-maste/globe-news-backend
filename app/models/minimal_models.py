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
    
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="category_rel")

class Source(Base):
    __tablename__ = "sources"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reliability_score: Mapped[int] = mapped_column(Integer, default=5)
    
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="source_rel")

class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI-generated 6-paragraph summary fields
    ai_summary_1: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_3: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_4: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_5: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_6: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_summary_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    full_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Foreign keys
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sources.id"))
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"))
    
    # Additional fields
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_rel: Mapped[Optional["Source"]] = relationship("Source", back_populates="articles")
    category_rel: Mapped[Optional["Category"]] = relationship("Category", back_populates="articles")
