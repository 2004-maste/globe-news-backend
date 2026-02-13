"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Dict
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Globe News"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./globe_news.db"
    
    # RSS Feeds Configuration
    RSS_FEEDS: List[Dict[str, str]] = [
        # English Sources
        {
            "name": "BBC World",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "language": "en",
            "category": "World"
        },
        {
            "name": "BBC Technology",
            "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", 
            "language": "en",
            "category": "Technology"
        },
        {
            "name": "BBC Business",
            "url": "http://feeds.bbci.co.uk/news/business/rss.xml",
            "language": "en", 
            "category": "Business"
        },
        {
            "name": "Reuters World",
            "url": "http://feeds.reuters.com/Reuters/worldNews",
            "language": "en",
            "category": "World"
        },
        {
            "name": "Reuters Technology",
            "url": "http://feeds.reuters.com/reuters/technologyNews",
            "language": "en",
            "category": "Technology"
        },
        
        # Kinyarwanda Sources
        {
            "name": "IGIHE",
            "url": "https://en.igihe.com/rss",
            "language": "rw",
            "category": "General"
        },
        {
            "name": "New Times Rwanda",
            "url": "https://www.newtimes.co.rw/rss",
            "language": "rw", 
            "category": "General"
        },
        {
            "name": "KT Press",
            "url": "https://www.ktpress.rw/feed/",
            "language": "rw",
            "category": "General"
        },
        {
            "name": "BBC Gahuza",
            "url": "https://www.bbc.com/gahuza/afs/feed",
            "language": "rw",
            "category": "World"
        }
    ]
    
    # News fetching interval (in seconds)
    FETCH_INTERVAL: int = 3600  # 1 hour
    
    # Summarization settings
    SUMMARY_LENGTH: int = 6  # Number of paragraphs
    SUMMARY_SENTENCES_PER_PARAGRAPH: int = 2
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    class Config:
        env_file = ".env"

settings = Settings()