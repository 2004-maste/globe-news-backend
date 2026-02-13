"""
RSS Feed Fetcher for news articles
"""
import feedparser
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
import html
import re

logger = logging.getLogger(__name__)

class RSSFetcher:
    """Fetches and parses RSS feeds from news sources"""
    
    def __init__(self):
        self.feeds_processed = 0
        self.articles_fetched = 0
    
    def parse_feed(self, feed_url: str, source_name: str, category: str = "General") -> List[Dict]:
        """
        Parse an RSS feed and extract articles
        
        Args:
            feed_url: URL of the RSS feed
            source_name: Name of the news source
            category: Category for the articles
            
        Returns:
            List of article dictionaries
        """
        try:
            logger.info(f"Parsing RSS feed: {source_name} - {feed_url}")
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing issue for {source_name}: {feed.bozo_exception}")
                return []
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 articles per feed
                try:
                    article = self._parse_entry(entry, source_name, category)
                    if article:
                        articles.append(article)
                        self.articles_fetched += 1
                except Exception as e:
                    logger.error(f"Error parsing entry from {source_name}: {e}")
                    continue
            
            self.feeds_processed += 1
            logger.info(f"Fetched {len(articles)} articles from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            return []
    
    def _parse_entry(self, entry, source_name: str, category: str) -> Optional[Dict]:
        """Parse a single RSS entry into article format"""
        try:
            # Extract title
            title = self._clean_text(getattr(entry, 'title', ''))
            if not title:
                return None
            
            # Extract content/summary
            summary = self._clean_text(getattr(entry, 'summary', ''))
            
            # Try to get full content from different fields
            content = ""
            if hasattr(entry, 'content') and entry.content:
                # Some feeds have content in content[0].value
                for item in entry.content:
                    if hasattr(item, 'value'):
                        content = self._clean_text(item.value)
                        break
            
            if not content and hasattr(entry, 'description'):
                content = self._clean_text(entry.description)
            
            # Use summary if no content
            if not content and summary:
                content = summary
            elif not summary and content:
                # Use first 200 chars of content as summary
                summary = content[:200] + "..." if len(content) > 200 else content
            
            # Extract link
            link = getattr(entry, 'link', '')
            if not link:
                return None
            
            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed'):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed'):
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published = datetime.utcnow()
            
            # Extract image
            image_url = self._extract_image(entry)
            
            # Extract author
            author = ""
            if hasattr(entry, 'author'):
                author = self._clean_text(entry.author)
            
            # Create article dictionary
            article = {
                "title": title,
                "summary": summary[:500] if summary else "",  # Limit summary length
                "full_content": content,
                "url": link,
                "image_url": image_url,
                "published_at": published,
                "author": author,
                "source_name": source_name,
                "category": category,
                "language": "en",  # Default to English
                "is_trending": False,
                "is_breaking": False,
                "view_count": 0
            }
            
            return article
            
        except Exception as e:
            logger.error(f"Error in _parse_entry: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML and normalize text"""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        return text.strip()
    
    def _extract_image(self, entry) -> Optional[str]:
        """Extract image URL from RSS entry"""
        # Try different fields for images
        image_fields = [
            ('media_content', 'url'),  # Media RSS
            ('media_thumbnail', 'url'),  # Media RSS thumbnail
            ('enclosures', 'href'),  # Enclosures
        ]
        
        for field, attr in image_fields:
            if hasattr(entry, field):
                media = getattr(entry, field)
                if media:
                    if isinstance(media, list):
                        for item in media:
                            if hasattr(item, attr):
                                url = getattr(item, attr)
                                if url and url.startswith(('http://', 'https://')):
                                    return url
        
        # Try to find image in content
        if hasattr(entry, 'content') and entry.content:
            for item in entry.content:
                if hasattr(item, 'value'):
                    # Look for img tags
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', item.value)
                    if img_match:
                        return img_match.group(1)
        
        return None
    
    def fetch_multiple_feeds(self, feeds: List[Dict]) -> List[Dict]:
        """
        Fetch multiple RSS feeds
        
        Args:
            feeds: List of feed dictionaries with url, name, category
            
        Returns:
            Combined list of articles
        """
        all_articles = []
        
        for feed in feeds:
            articles = self.parse_feed(
                feed['url'],
                feed['name'],
                feed.get('category', 'General')
            )
            all_articles.extend(articles)
        
        logger.info(f"Total: Fetched {len(all_articles)} articles from {len(feeds)} feeds")
        return all_articles