"""
Unified Models for Globe News
Combines all model definitions in one place
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String, unique=True, nullable=False)
    url_to_image = Column(String)
    published_at = Column(DateTime)
    content = Column(Text)  # RSS snippet
    full_content = Column(Text)  # Extracted full article
    preview_content = Column(Text)  # Enhanced preview/analysis
    
    category_id = Column(Integer, ForeignKey("categories.id"))
    source = Column(String)
    author = Column(String)
    language = Column(String, default="en")  # 'en' or 'rw'
    is_breaking = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    has_full_content = Column(Boolean, default=False)
    content_length = Column(Integer, default=0)
    
    # New fields for admin approval (AdSense compliance)
    is_approved = Column(Boolean, default=False)  # Whether article is approved for public
    is_rejected = Column(Boolean, default=False)   # Whether article was rejected
    is_edited = Column(Boolean, default=False)     # Whether article was manually edited
    
    approved_at = Column(DateTime, nullable=True)   # When approved
    approved_by = Column(String, nullable=True)     # Who approved
    rejected_at = Column(DateTime, nullable=True)   # When rejected
    rejected_by = Column(String, nullable=True)     # Who rejected
    edited_at = Column(DateTime, nullable=True)     # Last edit time
    edited_by = Column(String, nullable=True)       # Who last edited
    
    # Editorial notes
    editor_notes = Column(Text, nullable=True)      # Internal notes for editors
    
    # Relationships
    category = relationship("Category", back_populates="articles")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_articles_language", "language"),
        Index("idx_articles_published", "published_at"),
        Index("idx_articles_category", "category_id"),
        Index("idx_articles_breaking", "is_breaking"),
        Index("idx_articles_approved", "is_approved"),  # New index for filtering
    )
    
    @property
    def is_public(self):
        """Check if article should be visible to public"""
        return self.is_approved and not self.is_rejected
    
    def __repr__(self):
        return f"<Article {self.title[:50]}...>"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.username}>"


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False)
    category = Column(String)
    language = Column(String, default="en")
    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime, nullable=True)
    fetch_frequency = Column(Integer, default=30)  # minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Source {self.name}>"


# For backward compatibility, you can add these aliases
# This will help existing imports work
MinimalModel = Base  # Just a reference, not typically needed
