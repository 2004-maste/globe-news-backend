"""
Main fetcher service that coordinates RSS and API fetching
"""
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .rss_fetcher import RSSFetcher
from .sources_manager import NewsSourcesManager
from .api_fetcher import APIFetcher
from ..models.minimal_models import Article, Source, Category
from ..database import SessionLocal

logger = logging.getLogger(__name__)

class NewsFetcherService:
    """Main service for fetching and storing news"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.rss_fetcher = RSSFetcher()
        self.sources_manager = NewsSourcesManager()
        self.api_fetcher = APIFetcher()
        
    def fetch_and_store_news(self, max_articles: int = 100) -> Dict:
        """
        Fetch news from all sources and store in database
        
        Args:
            max_articles: Maximum number of articles to fetch
            
        Returns:
            Dictionary with fetch results
        """
        logger.info("Starting news fetch operation...")
        
        all_articles = []
        results = {
            "rss_articles": 0,
            "api_articles": 0,
            "duplicates_skipped": 0,
            "new_articles_added": 0,
            "sources_updated": 0,
            "categories_updated": 0,
            "total_time": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Fetch from RSS feeds
            feeds = self.sources_manager.get_feeds_for_fetching(limit=15)
            rss_articles = self.rss_fetcher.fetch_multiple_feeds(feeds)
            results["rss_articles"] = len(rss_articles)
            all_articles.extend(rss_articles)
            
            # Step 2: Fetch from APIs
            api_articles = self.api_fetcher.fetch_all()
            results["api_articles"] = len(api_articles)
            all_articles.extend(api_articles)
            
            # Step 3: Ensure sources and categories exist
            self._ensure_sources_and_categories(all_articles)
            
            # Step 4: Filter duplicates and store new articles
            new_articles_added = 0
            for article_data in all_articles[:max_articles]:
                try:
                    if self._is_duplicate_article(article_data):
                        results["duplicates_skipped"] += 1
                        continue
                    
                    if self._store_article(article_data):
                        new_articles_added += 1
                        
                except Exception as e:
                    logger.error(f"Error processing article '{article_data.get('title', 'Unknown')}': {e}")
                    continue
            
            results["new_articles_added"] = new_articles_added
            
            # Step 5: Update trending/breaking status
            self._update_trending_status()
            
            end_time = datetime.utcnow()
            results["total_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"""
            📰 Fetch Results:
            • RSS Articles fetched: {results['rss_articles']}
            • API Articles fetched: {results['api_articles']}
            • Duplicates skipped: {results['duplicates_skipped']}
            • New articles added: {results['new_articles_added']}
            • Total time: {results['total_time']:.2f}s
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store_news: {e}")
            self.db.rollback()
            raise
        finally:
            if not self.db:
                self.db.close()
    
    def _ensure_sources_and_categories(self, articles: List[Dict]):
        """Ensure all sources and categories exist in database"""
        sources_added = 0
        categories_added = 0
        
        # Get unique sources and categories
        sources = {}
        categories = set()
        
        for article in articles:
            source_name = article.get("source_name", "")
            category = article.get("category", "General")

            if source_name:
                sources[source_name] = sources.get(source_name, {
                    "name": source_name,
                    "country": article.get("country", "Unknown"),
                    "language": article.get("language", "en"),
                    "reliability_score": 7
                })
            
            if category:
                categories.add(category)
        
        # Add categories
        for category_name in categories:
            existing = self.db.query(Category).filter(Category.name == category_name).first()
            if not existing:
                category = Category(
                    name=category_name,
                    description=f"News about {category_name}"
                )
                self.db.add(category)
                categories_added += 1
        
        # Add sources
        for source_data in sources.values():
            existing = self.db.query(Source).filter(Source.name == source_data["name"]).first()
            if not existing:
                source = Source(
                    name=source_data["name"],
                    country=source_data["country"],
                    language=source_data["language"],
                    reliability_score=source_data["reliability_score"]
                )
                self.db.add(source)
                sources_added += 1
        
        if sources_added or categories_added:
            self.db.commit()
            logger.info(f"Added {sources_added} new sources and {categories_added} new categories")
    
    def _is_duplicate_article(self, article_data: Dict) -> bool:
        """Check if article already exists in database"""
        title = article_data.get("title", "")
        url = article_data.get("url", "")
        
        if not title or not url:
            return True
        
        # Check by URL (most reliable)
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            return True
        
        # Check by similar title (fuzzy match)
        existing = self.db.query(Article).filter(
            Article.title.ilike(f"%{title[:50]}%")
        ).first()
        
        return existing is not None
    
    def _store_article(self, article_data: Dict) -> bool:
        """Store article in database"""
        try:
            # Get source
            source_name = article_data.get("source_name", "")
            source = self.db.query(Source).filter(Source.name == source_name).first()
            if not source:
                logger.warning(f"Source not found: {source_name}")
                return False
            
            # Get category
            category_name = article_data.get("category", "General")
            category = self.db.query(Category).filter(Category.name == category_name).first()
            if not category:
                # Create category if it doesn't exist
                category = Category(name=category_name, description=f"News about {category_name}")
                self.db.add(category)
                self.db.commit()
            
            # Create article
            article = Article(
                title=article_data["title"],
                summary=article_data.get("summary", ""),
                full_content=article_data.get("full_content", ""),
                url=article_data["url"],
                image_url=article_data.get("image_url", ""),
                published_at=article_data.get("published_at", datetime.utcnow()),
                author=article_data.get("author", ""),
                source_id=source.id,
                category_id=category.id,
                country=article_data.get("country", ""),
                language=article_data.get("language", "en"),
                is_trending=article_data.get("is_trending", False),
                is_breaking=article_data.get("is_breaking", False),
                view_count=article_data.get("view_count", 0)
            )
            
            self.db.add(article)
            self.db.commit()
            
            logger.debug(f"Stored article: {article_data['title'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article: {e}")
            self.db.rollback()
            return False
    
    def _update_trending_status(self):
        """Update trending and breaking status based on recency and engagement"""
        try:
            # Mark articles from last 24 hours as potentially trending
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            
            # Reset all trending/breaking flags first
            self.db.query(Article).update({
                "is_trending": False,
                "is_breaking": False
            })
            
            # Mark recent articles with high view counts as trending
            trending_articles = self.db.query(Article).filter(
                Article.published_at >= time_threshold,
                Article.view_count >= 10
            ).order_by(Article.view_count.desc()).limit(10).all()
            
            for article in trending_articles:
                article.is_trending = True
            
            # Mark very recent articles (last 2 hours) as breaking
            breaking_threshold = datetime.utcnow() - timedelta(hours=2)
            breaking_articles = self.db.query(Article).filter(
                Article.published_at >= breaking_threshold
            ).order_by(Article.published_at.desc()).limit(5).all()
            
            for article in breaking_articles:
                article.is_breaking = True
            
            self.db.commit()
            logger.info(f"Updated {len(trending_articles)} trending and {len(breaking_articles)} breaking articles")
            
        except Exception as e:
            logger.error(f"Error updating trending status: {e}")
            self.db.rollback()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            total_articles = self.db.query(Article).count()
            total_sources = self.db.query(Source).count()
            total_categories = self.db.query(Category).count()
            trending_articles = self.db.query(Article).filter(Article.is_trending == True).count()
            breaking_articles = self.db.query(Article).filter(Article.is_breaking == True).count()
            
            return {
                "total_articles": total_articles,
                "total_sources": total_sources,
                "total_categories": total_categories,
                "trending_articles": trending_articles,
                "breaking_articles": breaking_articles,
                "latest_fetch": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}