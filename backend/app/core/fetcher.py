"""
News Fetcher Module - Fetches real news from RSS feeds
"""
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import newspaper
from newspaper import Article as NewsArticle
import re

from ..models.article import Article, Category, NewsSource
from ..core.config import settings

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self, db: Session):
        self.db = db
        self.session = None
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_all_news(self):
        """Fetch news from all configured RSS feeds."""
        logger.info("Starting news fetch from all sources...")
        
        tasks = []
        for feed_config in settings.RSS_FEEDS:
            task = self.fetch_single_feed(feed_config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        saved_count = 0
        for result in results:
            if isinstance(result, list):
                saved_count += len(result)
        
        logger.info(f"Successfully fetched {saved_count} new articles")
        return saved_count
    
    async def fetch_single_feed(self, feed_config: Dict[str, str]) -> List[Article]:
        """Fetch and parse a single RSS feed."""
        try:
            logger.info(f"Fetching from {feed_config['name']}...")
            
            async with self.session.get(feed_config["url"], timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {feed_config['name']}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if not feed.entries:
                    logger.warning(f"No entries found in {feed_config['name']}")
                    return []
                
                articles = []
                for entry in feed.entries[:15]:  # Limit to 15 articles per feed
                    try:
                        article = await self.parse_feed_entry(entry, feed_config)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.error(f"Error parsing entry: {e}")
                        continue
                
                logger.info(f"Fetched {len(articles)} articles from {feed_config['name']}")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching {feed_config['name']}: {e}")
            return []
    
    async def parse_feed_entry(self, entry, feed_config: Dict[str, str]) -> Article:
        """Parse a single RSS feed entry into Article object."""
        # Get URL
        url = entry.link if hasattr(entry, 'link') else ''
        if not url:
            return None
        
        # Check if article already exists
        existing = self.db.query(Article).filter(Article.url == url).first()
        if existing:
            return None
        
        # Get published date
        published_at = self._parse_date(entry)
        
        # Only fetch recent articles (last 7 days)
        if datetime.now() - published_at > timedelta(days=7):
            return None
        
        # Get title and description
        title = entry.title if hasattr(entry, 'title') else 'No Title'
        description = entry.description if hasattr(entry, 'description') else ''
        
        # Get image URL
        image_url = self._extract_image_url(entry)
        
        # Fetch full content using newspaper3k
        content = await self._fetch_full_content(url)
        
        # Get or create category
        category_name = feed_config.get('category', 'General')
        category = self.db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(name=category_name, description=f"{category_name} news")
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
        
        # Create article
        article = Article(
            title=title[:500],
            description=description[:1000] if description else '',
            url=url[:500],
            url_to_image=image_url[:500] if image_url else None,
            published_at=published_at,
            content=content[:10000] if content else '',
            category_id=category.id,
            source=feed_config['name'],
            author=entry.author if hasattr(entry, 'author') else feed_config['name'],
            language=feed_config['language'],
            is_fetched=True
        )
        
        self.db.add(article)
        try:
            self.db.commit()
            self.db.refresh(article)
            return article
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            self.db.rollback()
            return None
    
    def _parse_date(self, entry):
        """Parse date from feed entry."""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except:
            pass
        
        return datetime.now()
    
    def _extract_image_url(self, entry):
        """Extract image URL from feed entry."""
        try:
            # Check for media content
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if media.get('type', '').startswith('image/'):
                        return media.get('url')
            
            # Check for media thumbnail
            if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                return entry.media_thumbnail[0].get('url')
            
            # Check for enclosure
            if hasattr(entry, 'enclosures') and entry.enclosures:
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('image/'):
                        return enc.get('href')
            
            # Extract from description HTML
            if hasattr(entry, 'description'):
                import re
                img_match = re.search(r'<img[^>]+src="([^">]+)"', entry.description)
                if img_match:
                    return img_match.group(1)
        
        except Exception as e:
            logger.debug(f"Error extracting image: {e}")
        
        return None
    
    async def _fetch_full_content(self, url: str) -> str:
        """Fetch full article content using newspaper3k."""
        try:
            # Configure newspaper
            config = newspaper.Config()
            config.browser_user_agent = self.user_agent
            config.request_timeout = 10
            config.memoize_articles = False
            
            # Download and parse article
            article = NewsArticle(url, config=config)
            article.download()
            article.parse()
            
            content = article.text
            if content and len(content) > 100:
                return content[:5000]  # Limit content length
            
        except Exception as e:
            logger.debug(f"Could not fetch full content for {url}: {e}")
        
        return ""