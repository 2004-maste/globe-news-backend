"""
Articles API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional, List
from datetime import datetime, timedelta

from ....database import get_db
from ....models.article import Article, Category

router = APIRouter()

@router.get("")
async def get_articles(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    breaking: bool = False
):
    """Get articles with filtering."""
    try:
        query = db.query(Article)
        
        # Apply category filter
        if category:
            category_obj = db.query(Category).filter(Category.name == category).first()
            if category_obj:
                query = query.filter(Article.category_id == category_obj.id)
        
        # Apply language filter
        if language and language != "all":
            query = query.filter(Article.language == language)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Article.title.ilike(search_term),
                    Article.description.ilike(search_term),
                    Article.content.ilike(search_term)
                )
            )
        
        # Apply breaking news filter (last 24 hours)
        if breaking:
            time_threshold = datetime.now() - timedelta(hours=24)
            query = query.filter(Article.published_at >= time_threshold)
        
        # Order by most recent
        query = query.order_by(desc(Article.published_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        articles = query.offset(skip).limit(limit).all()
        
        # Convert to dict with category names
        result = []
        for article in articles:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "url": article.url,
                "url_to_image": article.url_to_image,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "content": article.content,
                "summary": article.summary,
                "category_id": article.category_id,
                "category_name": article.category.name if article.category else "General",
                "source": article.source,
                "author": article.author,
                "language": article.language,
                "is_breaking": article.is_breaking,
                "created_at": article.created_at.isoformat() if article.created_at else None
            }
            result.append(article_dict)
        
        return {
            "articles": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching articles: {str(e)}")

@router.get("/{article_id}")
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get single article by ID."""
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get related articles (same category)
        related = db.query(Article).filter(
            Article.category_id == article.category_id,
            Article.id != article.id,
            Article.language == article.language
        ).order_by(desc(Article.published_at)).limit(5).all()
        
        related_list = []
        for rel in related:
            related_list.append({
                "id": rel.id,
                "title": rel.title,
                "description": rel.description,
                "url_to_image": rel.url_to_image,
                "published_at": rel.published_at.isoformat() if rel.published_at else None,
                "category_name": rel.category.name if rel.category else "General",
                "language": rel.language
            })
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "url_to_image": article.url_to_image,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "content": article.content,
            "summary": article.summary,
            "category_id": article.category_id,
            "category_name": article.category.name if article.category else "General",
            "source": article.source,
            "author": article.author,
            "language": article.language,
            "is_breaking": article.is_breaking,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "related_articles": related_list
        }
        
        return article_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching article: {str(e)}")

@router.get("/trending/")
async def get_trending_articles(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get trending articles (last 3 days)."""
    try:
        time_threshold = datetime.now() - timedelta(days=3)
        
        articles = db.query(Article).filter(
            Article.published_at >= time_threshold
        ).order_by(desc(Article.published_at)).limit(limit).all()
        
        result = []
        for article in articles:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "url_to_image": article.url_to_image,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "category_name": article.category.name if article.category else "General",
                "source": article.source,
                "language": article.language
            }
            result.append(article_dict)
        
        return {
            "articles": result,
            "count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending articles: {str(e)}")