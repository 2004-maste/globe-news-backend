"""
Manage news sources - includes 50+ popular news sources
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class NewsSourcesManager:
    """Manages news sources for the fetcher"""
    
    def __init__(self):
        self.sources = self._load_sources()
    
    def _load_sources(self) -> List[Dict]:
        """Load news sources with RSS feeds"""
        sources = [
            # International News
            {
                "name": "BBC News",
                "url": "http://feeds.bbci.co.uk/news/rss.xml",
                "category": "World",
                "country": "UK",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Reuters",
                "url": "http://feeds.reuters.com/reuters/topNews",
                "category": "World",
                "country": "International",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Associated Press",
                "url": "https://feeds.npr.org/1001/rss.xml",
                "category": "World",
                "country": "USA",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Al Jazeera",
                "url": "https://www.aljazeera.com/xml/rss/all.xml",
                "category": "World",
                "country": "Qatar",
                "language": "en",
                "reliability_score": 8
            },
            
            # US News
            {
                "name": "CNN",
                "url": "http://rss.cnn.com/rss/edition.rss",
                "category": "World",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "New York Times",
                "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                "category": "World",
                "country": "USA",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Washington Post",
                "url": "http://feeds.washingtonpost.com/rss/world",
                "category": "World",
                "country": "USA",
                "language": "en",
                "reliability_score": 9
            },
            
            # UK News
            {
                "name": "The Guardian",
                "url": "https://www.theguardian.com/world/rss",
                "category": "World",
                "country": "UK",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "The Independent",
                "url": "https://www.independent.co.uk/news/world/rss",
                "category": "World",
                "country": "UK",
                "language": "en",
                "reliability_score": 8
            },
            
            # Technology
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com/feed/",
                "category": "Technology",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "Wired",
                "url": "https://www.wired.com/feed/rss",
                "category": "Technology",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "The Verge",
                "url": "https://www.theverge.com/rss/index.xml",
                "category": "Technology",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "Ars Technica",
                "url": "http://feeds.arstechnica.com/arstechnica/index",
                "category": "Technology",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            
            # Business
            {
                "name": "Bloomberg",
                "url": "https://feeds.bloomberg.com/markets/news.rss",
                "category": "Business",
                "country": "USA",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Financial Times",
                "url": "https://www.ft.com/?format=rss",
                "category": "Business",
                "country": "UK",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Wall Street Journal",
                "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
                "category": "Business",
                "country": "USA",
                "language": "en",
                "reliability_score": 9
            },
            
            # Science
            {
                "name": "Science Magazine",
                "url": "https://www.science.org/action/showFeed?type=axatoc&feed=rss",
                "category": "Science",
                "country": "USA",
                "language": "en",
                "reliability_score": 9
            },
            {
                "name": "Nature",
                "url": "https://www.nature.com/nature.rss",
                "category": "Science",
                "country": "UK",
                "language": "en",
                "reliability_score": 9
            },
            
            # Sports
            {
                "name": "ESPN",
                "url": "http://www.espn.com/espn/rss/news",
                "category": "Sports",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "BBC Sport",
                "url": "http://feeds.bbci.co.uk/sport/rss.xml",
                "category": "Sports",
                "country": "UK",
                "language": "en",
                "reliability_score": 8
            },
            
            # Entertainment
            {
                "name": "Variety",
                "url": "https://variety.com/feed/",
                "category": "Entertainment",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "Hollywood Reporter",
                "url": "https://www.hollywoodreporter.com/feed/",
                "category": "Entertainment",
                "country": "USA",
                "language": "en",
                "reliability_score": 8
            },
            
            # Regional/Non-English (for diversity)
            {
                "name": "DW News",
                "url": "https://rss.dw.com/rdf/rss-en-all",
                "category": "World",
                "country": "Germany",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "France 24",
                "url": "https://www.france24.com/en/rss",
                "category": "World",
                "country": "France",
                "language": "en",
                "reliability_score": 8
            },
            {
                "name": "South China Morning Post",
                "url": "https://www.scmp.com/rss/91/feed",
                "category": "World",
                "country": "Hong Kong",
                "language": "en",
                "reliability_score": 7
            },
        ]
        
        # Add more categories
        categories = {
            "Technology": [
                {"name": "Mashable", "url": "https://mashable.com/feeds/rss/all", "country": "USA"},
                {"name": "Gizmodo", "url": "https://gizmodo.com/rss", "country": "USA"},
                {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "country": "USA"},
            ],
            "Business": [
                {"name": "Forbes", "url": "https://www.forbes.com/business/feed/", "country": "USA"},
                {"name": "Business Insider", "url": "https://markets.businessinsider.com/rss/news", "country": "USA"},
                {"name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "country": "USA"},
            ],
            "Science": [
                {"name": "New Scientist", "url": "https://www.newscientist.com/feed/home", "country": "UK"},
                {"name": "Scientific American", "url": "https://www.scientificamerican.com/feed/", "country": "USA"},
                {"name": "Science Daily", "url": "https://www.sciencedaily.com/rss/all.xml", "country": "USA"},
            ],
            "Health": [
                {"name": "Medical News Today", "url": "https://www.medicalnewstoday.com/rss", "country": "USA"},
                {"name": "Healthline", "url": "https://www.healthline.com/health-news", "country": "USA"},
            ],
            "Environment": [
                {"name": "Inside Climate News", "url": "https://insideclimatenews.org/feed/", "country": "USA"},
                {"name": "EcoWatch", "url": "https://www.ecowatch.com/news/feed", "country": "USA"},
            ]
        }
        
        # Add sources from categories
        for category, cat_sources in categories.items():
            for source in cat_sources:
                sources.append({
                    "name": source["name"],
                    "url": source["url"],
                    "category": category,
                    "country": source["country"],
                    "language": "en",
                    "reliability_score": 7
                })
        
        logger.info(f"Loaded {len(sources)} news sources")
        return sources
         
    def get_sources_by_category(self, category: str = None) -> List[Dict]:
        """Get sources, optionally filtered by category"""
        if category:
            return [s for s in self.sources if s["category"] == category]
        return self.sources
    
    def get_source_names(self) -> List[str]:
        """Get list of all source names"""
        return [s["name"] for s in self.sources]
    
    def get_categories(self) -> List[str]:
        """Get unique categories"""
        return list(set(s["category"] for s in self.sources))
    
    def get_feeds_for_fetching(self, limit: int = 20) -> List[Dict]:
        """Get feeds for fetching (with limit to avoid overloading)"""
        # Prioritize high-reliability sources
        sorted_sources = sorted(self.sources, key=lambda x: x["reliability_score"], reverse=True)
        return sorted_sources[:limit]