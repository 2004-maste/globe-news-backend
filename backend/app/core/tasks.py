"""
Background Tasks for automatic news fetching
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from .fetcher import NewsFetcher
from .summarizer import ArticleSummarizer
from ..models.article import Article

logger = logging.getLogger(__name__)

async def fetch_news_periodically():
    """Periodically fetch news from RSS feeds."""
    logger.info("Starting periodic news fetcher...")
    
    while True:
        try:
            await fetch_latest_news()
            
            # Wait for 1 hour before next fetch
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in periodic news fetch: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

async def fetch_latest_news():
    """Fetch latest news from all sources."""
    db = SessionLocal()
    try:
        async with NewsFetcher(db) as fetcher:
            count = await fetcher.fetch_all_news()
            
            if count > 0:
                logger.info(f"Fetched {count} new articles, generating summaries...")
                await generate_summaries_for_new_articles(db)
            
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
    finally:
        db.close()

async def generate_summaries_for_new_articles(db: Session):
    """Generate AI summaries for new articles."""
    try:
        # Get articles without summaries from the last 24 hours
        time_threshold = datetime.now() - timedelta(hours=24)
        articles = db.query(Article).filter(
            Article.summary == None,
            Article.published_at >= time_threshold,
            Article.content != None,
            Article.content != ''
        ).all()
        
        summarizer = ArticleSummarizer()
        
        for article in articles:
            try:
                summary = summarizer.summarize_article(
                    article.title,
                    article.content,
                    article.language
                )
                
                if summary:
                    article.summary = summary
                    db.commit()
                    logger.info(f"Generated summary for article: {article.id}")
                    
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error generating summary for article {article.id}: {e}")
                continue
        
        logger.info(f"Generated summaries for {len(articles)} articles")
        
    except Exception as e:
        logger.error(f"Error in summary generation: {e}")

async def start_background_tasks():
    """Start all background tasks."""
    # Initial fetch
    await fetch_latest_news()
    
    # Start periodic fetching
    asyncio.create_task(fetch_news_periodically())