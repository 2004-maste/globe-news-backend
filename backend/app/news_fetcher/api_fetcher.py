"""
API-based news fetcher (NewsAPI, GNews, etc.)
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class APIFetcher:
    """Fetches news from various APIs"""
    
    def __init__(self):
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self.gnews_key = os.getenv("GNEWS_API_KEY", "")
        
    def fetch_from_newsapi(self, query: str = "", category: str = "general", 
                          language: str = "en", page_size: int = 20) -> List[Dict]:
        """Fetch news from NewsAPI"""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not set. Skipping NewsAPI fetch.")
            return []
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.newsapi_key,
                "language": language,
                "pageSize": page_size
            }
            
            if query:
                params["q"] = query
            if category:
                params["category"] = category
            
            logger.info(f"Fetching from NewsAPI: {category}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                formatted_articles = []
                for article in articles:
                    formatted = self._format_newsapi_article(article, category)
                    if formatted:
                        formatted_articles.append(formatted)
                
                logger.info(f"Fetched {len(formatted_articles)} articles from NewsAPI")
                return formatted_articles
            else:
                logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []
    
    def _format_newsapi_article(self, article: Dict, category: str) -> Optional[Dict]:
        """Format NewsAPI article to our format"""
        try:
            title = article.get("title", "").strip()
            if not title or title.lower() == "[removed]":
                return None
            
            published_str = article.get("publishedAt", "")
            published = None
            if published_str:
                try:
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except:
                    published = datetime.utcnow()
            else:
                published = datetime.utcnow()
            
            return {
                "title": title,
                "summary": article.get("description", "")[:500],
                "full_content": article.get("content", "") or article.get("description", ""),
                "url": article.get("url", ""),
                "image_url": article.get("urlToImage", ""),
                "published_at": published,
                "author": article.get("author", ""),
                "source_name": article.get("source", {}).get("name", "Unknown"),
                "category": category,
                "language": "en",
                "is_trending": False,
                "is_breaking": False,
                "view_count": 0
            }
        except Exception as e:
            logger.error(f"Error formatting NewsAPI article: {e}")
            return None
    
    def fetch_from_gnews(self, query: str = "", category: str = "general",
                        language: str = "en", max_articles: int = 20) -> List[Dict]:
        """Fetch news from GNews API"""
        if not self.gnews_key:
            logger.warning("GNews API key not set. Skipping GNews fetch.")
            return []
        
        try:
            url = "https://gnews.io/api/v4/top-headlines"
            params = {
                "token": self.gnews_key,
                "lang": language,
                "max": max_articles
            }
            
            if query:
                params["q"] = query
            if category and category != "general":
                params["topic"] = category
            
            logger.info(f"Fetching from GNews: {category}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                formatted_articles = []
                for article in articles:
                    formatted = self._format_gnews_article(article, category)
                    if formatted:
                        formatted_articles.append(formatted)
                
                logger.info(f"Fetched {len(formatted_articles)} articles from GNews")
                return formatted_articles
            else:
                logger.error(f"GNews error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from GNews: {e}")
            return []
    
    def _format_gnews_article(self, article: Dict, category: str) -> Optional[Dict]:
        """Format GNews article to our format"""
        try:
            title = article.get("title", "").strip()
            if not title:
                return None
            
            published_str = article.get("publishedAt", "")
            published = None
            if published_str:
                try:
                    # GNews format: "2024-01-15T10:30:00Z"
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except:
                    published = datetime.utcnow()
            else:
                published = datetime.utcnow()
            
            return {
                "title": title,
                "summary": article.get("description", "")[:500],
                "full_content": article.get("content", "") or article.get("description", ""),
                "url": article.get("url", ""),
                "image_url": article.get("image", ""),
                "published_at": published,
                "author": article.get("source", {}).get("name", "Unknown"),
                "source_name": article.get("source", {}).get("name", "Unknown"),
                "category": category,
                "language": "en",
                "is_trending": False,
                "is_breaking": False,
                "view_count": 0
            }
        except Exception as e:
            logger.error(f"Error formatting GNews article: {e}")
            return None
    
    def fetch_all(self, categories: List[str] = None) -> List[Dict]:
        """Fetch from all available APIs"""
        all_articles = []
        
        if categories is None:
            categories = ["general", "technology", "business", "science", "sports", "entertainment"]
        
        for category in categories:
            # Fetch from NewsAPI
            newsapi_articles = self.fetch_from_newsapi(category=category)
            all_articles.extend(newsapi_articles)
            
            # Fetch from GNews
            gnews_articles = self.fetch_from_gnews(category=category)
            all_articles.extend(gnews_articles)
            
            # Avoid rate limiting
            import time
            time.sleep(1)
        
        logger.info(f"Total fetched from APIs: {len(all_articles)} articles")
        return all_articles