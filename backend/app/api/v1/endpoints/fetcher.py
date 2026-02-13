from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ....database import get_db
from ....models.article import Article, NewsSource
from ....core.tasks import fetch_latest_news
from ....core.config import settings

router = APIRouter()

@router.get("/stats")
async def get_fetcher_stats(db: Session = Depends(get_db)):
    total = db.query(Article).count()
    english = db.query(Article).filter(Article.language == "en").count()
    kinyarwanda = db.query(Article).filter(Article.language == "rw").count()
    
    # Latest article
    latest = db.query(Article).order_by(Article.published_at.desc()).first()
    
    return {
        "total_articles": total,
        "english_articles": english,
        "kinyarwanda_articles": kinyarwanda,
        "latest_article_date": latest.published_at.isoformat() if latest else None,
        "configured_sources": len(settings.RSS_FEEDS),
        "last_updated": "Now"
    }

@router.get("/sources")
async def get_sources():
    return {
        "sources": settings.RSS_FEEDS,
        "count": len(settings.RSS_FEEDS)
    }

@router.post("/fetch-now")
async def fetch_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_latest_news)
    return {
        "message": "News fetch started in background",
        "status": "processing"
    }