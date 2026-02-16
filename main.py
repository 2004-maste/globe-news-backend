"""
Globe News Backend - Complete Version With Enhanced Previews
Original Code Base: Globe News Project v6.0.0
Content Extraction Enhancement: Added full article fetching using readability-lxml
This enhancement follows standard web scraping practices for news aggregation
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.routes import admin
import aiohttp
import feedparser
import asyncio
import sqlite3
import logging
from contextlib import asynccontextmanager
import re
import random
import html
import ssl
from app.database import init_db

# ✅ NEW: Import for content extraction (install with: pip install readability-lxml)
try:
    from readability import Document
except ImportError:
    Document = None
    print("⚠️  readability-lxml not installed. Run: pip install readability-lxml")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== DATABASE SETUP ====================

DB_PATH = os.environ.get('DB_PATH', '/app/data/globe_news.db')

def init_database():
    """Initialize SQLite database with proper schema and handle upgrades."""
    try:
        logger.info("Initializing database...")
        conn = sqlite3.connect('/app/data/globe_news.db')
        cursor = conn.cursor()
        
        # Create categories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create articles table with proper schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE NOT NULL,
            url_to_image TEXT,
            published_at TIMESTAMP NOT NULL,
            content TEXT,
            full_content TEXT,
            preview_content TEXT,
            category_id INTEGER,
            source TEXT,
            author TEXT,
            language TEXT DEFAULT 'en',
            is_breaking BOOLEAN DEFAULT 0,
            is_approved BOOLEAN DEFAULT 0,
            is_rejected BOOLEAN DEFAULT 0,
            is_edited BOOLEAN DEFAULT 0,
            approved_at DATETIME,
            approved_by TEXT,
            rejected_at DATETIME,
            rejected_by TEXT,
            edited_at DATETIME,
            edited_by TEXT,
            editor_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        ''')
        
        # Check and add missing columns
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # List of expected columns
        expected_columns = [
            ('preview_content', 'TEXT'),
            ('full_content', 'TEXT'),
            ('is_breaking', 'BOOLEAN DEFAULT 0'),
            ('is_approved', 'BOOLEAN DEFAULT 0'),
            ('is_rejected', 'BOOLEAN DEFAULT 0'),
            ('is_edited', 'BOOLEAN DEFAULT 0'),
            ('approved_at', 'DATETIME'),
            ('approved_by', 'TEXT'),
            ('rejected_at', 'DATETIME'),
            ('rejected_by', 'TEXT'),
            ('edited_at', 'DATETIME'),
            ('edited_by', 'TEXT'),
            ('editor_notes', 'TEXT')
        ]
        
        for column_name, column_type in expected_columns:
            if column_name not in existing_columns:
                logger.info(f"Adding missing column: {column_name}")
                try:
                    cursor.execute(f'ALTER TABLE articles ADD COLUMN {column_name} {column_type}')
                except Exception as e:
                    logger.warning(f"Could not add column {column_name}: {e}")
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_language ON articles(language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_approved ON articles(is_approved)')
        
        # Insert default categories
        default_categories = [
            ('World', 'International news'),
            ('Technology', 'Tech news and innovations'),
            ('Business', 'Business and economy'),
            ('Science', 'Scientific discoveries'),
            ('Entertainment', 'Movies, music, and arts'),
            ('Sports', 'Sports news'),
            ('Health', 'Health and medicine'),
            ('Politics', 'Political news'),
            ('General', 'General news')
        ]
        
        for name, description in default_categories:
            cursor.execute(
                'INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)',
                (name, description)
            )
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('/app/data/globe_news.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== UPDATED RSS FEEDS CONFIGURATION ====================

RSS_FEEDS = [
    # ========== INTERNATIONAL SOURCES ==========
    {
        'name': 'BBC Top Stories',
        'url': 'https://feeds.bbci.co.uk/news/rss.xml',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'BBC World',
        'url': 'https://feeds.bbci.co.uk/news/world/rss.xml',
        'language': 'en',
        'category': 'World',
        'extract_content': True
    },
    {
        'name': 'BBC Technology',
        'url': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
        'language': 'en',
        'category': 'Technology',
        'extract_content': True
    },
    {
        'name': 'BBC Business',
        'url': 'https://feeds.bbci.co.uk/news/business/rss.xml',
        'language': 'en',
        'category': 'Business',
        'extract_content': True
    },
    {
        'name': 'Reuters World',
        'url': 'https://www.reuters.com/arc/outboundfeeds/rss/?outputType=xml',
        'language': 'en',
        'category': 'World',
        'extract_content': True
    },
    {
        'name': 'Reuters Business',
        'url': 'https://www.reuters.com/arc/outboundfeeds/rss/?outputType=xml&feedName=businessNews',
        'language': 'en',
        'category': 'Business',
        'extract_content': True
    },
    {
        'name': 'AP News Top',
        'url': 'https://apnews.com/apf-topnews',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'CNN Top Stories',
        'url': 'http://rss.cnn.com/rss/edition.rss',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'Al Jazeera',
        'url': 'https://www.aljazeera.com/xml/rss/all.xml',
        'language': 'en',
        'category': 'World',
        'extract_content': True
    },
    {
        'name': 'The Guardian',
        'url': 'https://www.theguardian.com/world/rss',
        'language': 'en',
        'category': 'World',
        'extract_content': True
    },
    {
        'name': 'TechCrunch',
        'url': 'https://techcrunch.com/feed/',
        'language': 'en',
        'category': 'Technology',
        'extract_content': True
    },
    {
        'name': 'Wired',
        'url': 'https://www.wired.com/feed/rss',
        'language': 'en',
        'category': 'Technology',
        'extract_content': True
    },
    {
        'name': 'Bloomberg',
        'url': 'https://feeds.bloomberg.com/markets/news.rss',
        'language': 'en',
        'category': 'Business',
        'extract_content': True
    },
    
    # ========== AFRICAN & RWANDAN SOURCES ==========
    {
        'name': 'IGIHE',
        'url': 'https://en.igihe.com/rss',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'New Times Rwanda',
        'url': 'https://www.newtimes.co.rw/rss',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'KT Press',
        'url': 'https://www.ktpress.rw/feed/',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'BBC News Kinyarwanda',
        'url': 'https://www.bbc.com/gahuza/rss.xml',
        'language': 'rw',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'AllAfrica',
        'url': 'https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf',
        'language': 'en',
        'category': 'World',
        'extract_content': True
    },
    {
        'name': 'Umusingi',
        'url': 'https://umusingi.com/feed/',
        'language': 'rw',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'Rwanda News Agency',
        'url': 'https://www.rnanews.com/rss',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'Kigali Today',
        'url': 'https://kigalitoday.com/feed/',
        'language': 'en',
        'category': 'General',
        'extract_content': True
    },
    {
        'name': 'The EastAfrican',
        'url': 'https://www.theeastafrican.co.ke/rss',
        'language': 'en',
        'category': 'World',
        'extract_content': True
    },
    {
        'name': 'RBA Rwanda',
        'url': 'https://www.rba.co.rw/rss',
        'language': 'rw',
        'category': 'General',
        'extract_content': True
    },
    
    # ========== SPORTS SOURCES ==========
    {
        'name': 'ESPN',
        'url': 'http://www.espn.com/espn/rss/news',
        'language': 'en',
        'category': 'Sports',
        'extract_content': True
    },
    {
        'name': 'BBC Sports',
        'url': 'https://feeds.bbci.co.uk/sport/rss.xml',
        'language': 'en',
        'category': 'Sports',
        'extract_content': True
    },
    
    # ========== HEALTH & SCIENCE ==========
    {
        'name': 'BBC Health',
        'url': 'https://feeds.bbci.co.uk/news/health/rss.xml',
        'language': 'en',
        'category': 'Health',
        'extract_content': True
    },
    {
        'name': 'Medical News Today',
        'url': 'https://www.medicalnewstoday.com/rss-feeds',
        'language': 'en',
        'category': 'Health',
        'extract_content': True
    },
    {
        'name': 'Science Daily',
        'url': 'https://www.sciencedaily.com/rss/all.xml',
        'language': 'en',
        'category': 'Science',
        'extract_content': True
    },
    
    # ========== ENTERTAINMENT ==========
    {
        'name': 'BBC Entertainment',
        'url': 'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
        'language': 'en',
        'category': 'Entertainment',
        'extract_content': True
    },
    {
        'name': 'Variety',
        'url': 'https://variety.com/feed/',
        'language': 'en',
        'category': 'Entertainment',
        'extract_content': True
    }
]

# ==================== FALLBACK ARTICLES ====================

FALLBACK_ARTICLES = [
    # English fallback articles
    {
        'title': 'Global Summit Addresses Climate Change Concerns',
        'description': 'World leaders gather to discuss urgent climate action measures and set new environmental targets.',
        'url': 'https://example.com/fallback1',
        'url_to_image': 'https://images.unsplash.com/photo-1611273426858-450d8e3c9fce?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'published_at': (datetime.now() - timedelta(hours=2)).isoformat(),
        'content': 'World leaders from across the globe convened today to address pressing climate change issues. The summit focused on reducing carbon emissions and transitioning to renewable energy sources. Experts emphasized the need for immediate action to prevent irreversible damage to ecosystems worldwide. Several nations committed to ambitious targets for carbon neutrality by 2050.',
        'source': 'BBC News',
        'author': 'Climate Reporter',
        'language': 'en',
        'category': 'World'
    },
    {
        'title': 'Tech Innovation Revolutionizes Healthcare',
        'description': 'New AI-powered medical devices are transforming patient care and diagnosis accuracy.',
        'url': 'https://example.com/fallback2',
        'url_to_image': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'published_at': (datetime.now() - timedelta(hours=5)).isoformat(),
        'content': 'Artificial intelligence is revolutionizing the healthcare industry with new diagnostic tools and treatment methods that improve patient outcomes. Hospitals are implementing AI systems that can analyze medical images with greater accuracy than human doctors. These advancements are reducing diagnostic errors and enabling earlier detection of diseases.',
        'source': 'Tech Review',
        'author': 'Health Tech Editor',
        'language': 'en',
        'category': 'Technology'
    },
    # Kinyarwanda fallback articles
    {
        'title': 'U Rwanda rwongera gukomeza iterambere mu bukungu',
        'description': 'U Rwanda rwongeye kwiyongera mu bukungu bwa mbere muri iki cyumweru.',
        'url': 'https://example.com/rw-fallback1',
        'url_to_image': 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        'published_at': (datetime.now() - timedelta(hours=3)).isoformat(),
        'content': 'U Rwanda rwongeye kwerekana iterambere rirambye mu bukungu, hirya no hino mu gihugu. Imikorere yubukungu ishoboye kwiyongera bitewe nubucuruzi bwimbere nubukungu bwa serivisi. Abanyamuryango benshi babona u Rwanda nkigihugu gishya cyane muri Afurika.',
        'source': 'IGIHE',
        'author': 'Umutangazamakuru',
        'language': 'rw',
        'category': 'Business'
    }
]

# ==================== ENHANCED NEWS FETCHER WITH CONTENT EXTRACTION ====================

class NewsFetcher:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.timeout = aiohttp.ClientTimeout(total=45)
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
    
    async def fetch_all_news(self):
        """Fetch news from all RSS feeds."""
        logger.info(f"Starting news fetch from {len(RSS_FEEDS)} sources...")
        
        total_fetched = 0
        
        # Fetch feeds one by one (simpler, more reliable)
        for feed in RSS_FEEDS:
            try:
                count = await self.fetch_single_feed(feed)
                total_fetched += count
                if count > 0:
                    logger.info(f"✓ Fetched {count} articles from {feed['name']}")
                else:
                    logger.warning(f"✗ No articles from {feed['name']}")
            except Exception as e:
                logger.error(f"Error fetching from {feed['name']}: {e}")
        
        # If no articles were fetched, add fallback articles
        if total_fetched == 0:
            logger.warning("No articles fetched from RSS feeds, adding fallback articles...")
            total_fetched = await self.add_fallback_articles()
        
        logger.info(f"Total fetched: {total_fetched} articles")
        return total_fetched
    
    async def fetch_single_feed(self, feed: Dict):
        """Fetch and process a single RSS feed."""
        try:
            async with aiohttp.ClientSession(
                headers=self.headers,
                timeout=self.timeout
            ) as session:
                logger.debug(f"Fetching {feed['name']} from {feed['url']}")
                
                try:
                    async with session.get(feed['url'], ssl=False) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch {feed['name']}: HTTP {response.status}")
                            return 0
                        
                        content = await response.text()
                except ssl.SSLError:
                    # Try without SSL verification
                    async with session.get(feed['url'], ssl=False) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch {feed['name']} (no SSL): HTTP {response.status}")
                            return 0
                        
                        content = await response.text()
                
                # Parse the feed
                parsed_feed = feedparser.parse(content)
                
                if not parsed_feed.entries:
                    logger.warning(f"No entries in {feed['name']}")
                    return 0
                
                saved_count = 0
                for entry in parsed_feed.entries[:10]:  # Limit to 10 articles per feed
                    try:
                        saved = await self.process_entry(entry, feed)
                        if saved:
                            saved_count += 1
                    except Exception as e:
                        logger.debug(f"Error processing entry from {feed['name']}: {e}")
                        continue
                
                return saved_count
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching {feed['name']}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error fetching feed {feed['name']}: {e}")
            return 0
    
    async def extract_full_content(self, url: str, description: str, source: str) -> str:
        """
        Extract full article content from URL using readability-lxml.
        Falls back to description if extraction fails.
        """
        # Don't extract for fallback or example URLs
        if 'example.com' in url or not url.startswith('http'):
            return description
        
        try:
            async with aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=25)
            ) as session:
                async with session.get(url, ssl=False) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch article content: HTTP {response.status}")
                        return description
                    
                    html_content = await response.text()
                    
                    # Use readability-lxml if available
                    if Document:
                        try:
                            doc = Document(html_content)
                            content = doc.summary()
                            
                            # Clean HTML tags
                            clean_content = re.sub(r'<[^>]+>', ' ', content)
                            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                            
                            if clean_content and len(clean_content) > len(description) + 100:
                                logger.debug(f"Extracted {len(clean_content)} chars from {url}")
                                return clean_content[:10000]  # Limit length
                        except Exception as e:
                            logger.debug(f"Readability extraction failed: {e}")
                    
                    # Fallback: Try to extract main content using patterns
                    return self._extract_content_fallback(html_content, description, source)
                    
        except Exception as e:
            logger.debug(f"Content extraction failed for {url}: {e}")
            return description
    
    def _extract_content_fallback(self, html_content: str, description: str, source: str) -> str:
        """Fallback content extraction using regex patterns."""
        try:
            # Common article content patterns
            patterns = [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class=["\'][^"\']*article["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*story["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*content["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*post-content["\'][^>]*>(.*?)</div>',
                r'<div[^>]*id=["\'][^"\']*content["\'][^>]*>(.*?)</div>'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
                    # Clean HTML tags
                    clean_content = re.sub(r'<[^>]+>', ' ', content)
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    if clean_content and len(clean_content) > len(description) + 50:
                        return clean_content[:8000]
            
            return description
        except Exception:
            return description
    
    async def process_entry(self, entry, feed: Dict) -> bool:
        """Process a single RSS entry with full content extraction."""
        # Get URL
        url = entry.get('link', '')
        if not url or len(url) < 10:
            return False
        
        # Check if article already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
        if cursor.fetchone():
            conn.close()
            return False
        
        # Get published date
        published_at = self._parse_date(entry)
        
        # Get title and description
        title = entry.get('title', 'No Title').strip()[:400]
        if not title or title == 'No Title':
            conn.close()
            return False
        
        description = entry.get('description', '').strip()[:500]
        if not description:
            description = entry.get('summary', '')[:500]
        
        # Extract full content
        full_content = description
        if feed.get('extract_content', True):
            try:
                full_content = await self.extract_full_content(url, description, feed['name'])
                if full_content and len(full_content) > len(description):
                    logger.debug(f"Extracted full content: {len(full_content)} chars for {title[:50]}...")
                else:
                    logger.debug(f"Using RSS description for {title[:50]}...")
            except Exception as e:
                logger.warning(f"Content extraction failed: {e}")
                full_content = description
        
        # Get image URL
        image_url = self._extract_image_url(entry, description)
        
        # Get or create category
        category_name = feed.get('category', 'General')
        cursor.execute('SELECT id, name FROM categories WHERE name = ?', (category_name,))
        category = cursor.fetchone()
        
        if not category:
            cursor.execute(
                'INSERT INTO categories (name, description) VALUES (?, ?)',
                (category_name, f'{category_name} news')
            )
            category_id = cursor.lastrowid
        else:
            category_id = category[0]
            category_name = category[1]
        
        # Get author
        author = entry.get('author', '')
        if not author:
            author = entry.get('publisher', feed['name'])
        
        # Save article WITH FULL CONTENT
        cursor.execute('''
            INSERT INTO articles (
                title, description, url, url_to_image, published_at,
                content, full_content, category_id, source, author, language,
                is_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title,
            description,
            url[:500],
            image_url[:500] if image_url else None,
            published_at.isoformat(),
            description[:2000],
            full_content[:15000] if full_content else description[:2000],
            category_id,
            feed['name'],
            author[:200],
            feed['language'],
            0  # is_approved = False by default
        ))
        
        article_id = cursor.lastrowid
        
        # Generate preview with FULL CONTENT
        try:
            preview = ContentAnalyzer.generate_preview(
                title=title,
                description=description,
                full_content=full_content[:10000] if full_content else description,
                category=category_name,
                source=feed['name'],
                published_date=published_at.isoformat(),
                url=url,
                author=author
            )
            
            cursor.execute(
                'UPDATE articles SET preview_content = ? WHERE id = ?',
                (preview, article_id)
            )
            logger.debug(f"Generated preview with full content for: {title[:50]}...")
        except Exception as e:
            logger.warning(f"Could not generate preview: {e}")
        
        conn.commit()
        conn.close()
        return True
    
    async def add_fallback_articles(self) -> int:
        """Add fallback articles when RSS feeds fail."""
        saved_count = 0
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Current date for unique URLs
        current_date = datetime.now().strftime("%Y%m%d%H%M%S")
        
        fallback_articles = [
            {
                'title': 'Global Tech Conference Announces AI Breakthroughs',
                'description': 'Major technology companies unveil new artificial intelligence innovations at annual conference.',
                'url': f'https://example.com/tech-{current_date}-1',
                'url_to_image': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                'published_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'content': 'Technology leaders from around the world gathered to discuss the latest advancements in artificial intelligence and machine learning.',
                'category': 'Technology',
                'source': 'Tech News',
                'author': 'Technology Reporter',
                'language': 'en'
            },
            {
                'title': 'Stock Markets Reach New Highs Amid Economic Optimism',
                'description': 'Global financial markets show strong performance as economic indicators improve.',
                'url': f'https://example.com/business-{current_date}-2',
                'url_to_image': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                'published_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'content': 'Investors show increased confidence in global economic recovery as stock indices climb to record levels.',
                'category': 'Business',
                'source': 'Financial Times',
                'author': 'Business Analyst',
                'language': 'en'
            },
            {
                'title': 'Major Climate Agreement Reached at International Summit',
                'description': 'World leaders agree on new measures to address climate change concerns.',
                'url': f'https://example.com/world-{current_date}-3',
                'url_to_image': 'https://images.unsplash.com/photo-1611273426858-450d8e3c9fce?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                'published_at': (datetime.now() - timedelta(hours=3)).isoformat(),
                'content': 'International delegates have reached a consensus on new environmental policies aimed at reducing carbon emissions.',
                'category': 'World',
                'source': 'Global News',
                'author': 'Environmental Correspondent',
                'language': 'en'
            },
            {
                'title': 'New Medical Study Reveals Breakthrough in Cancer Treatment',
                'description': 'Researchers announce promising results from clinical trials of innovative therapy.',
                'url': f'https://example.com/health-{current_date}-4',
                'url_to_image': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                'published_at': (datetime.now() - timedelta(hours=4)).isoformat(),
                'content': 'Medical scientists report significant progress in developing new treatments for various cancer types.',
                'category': 'Health',
                'source': 'Medical Journal',
                'author': 'Health Reporter',
                'language': 'en'
            },
            {
                'title': 'National Team Wins Championship in International Tournament',
                'description': 'Sports victory celebrated nationwide after dramatic final match.',
                'url': f'https://example.com/sports-{current_date}-5',
                'url_to_image': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                'published_at': (datetime.now() - timedelta(hours=5)).isoformat(),
                'content': 'The national sports team secured a historic victory in the international championship finals.',
                'category': 'Sports',
                'source': 'Sports Network',
                'author': 'Sports Journalist',
                'language': 'en'
            },
            {
                'title': 'U Rwanda rwongera gukomeza iterambere mu bukungu',
                'description': 'U Rwanda rwongeye kwiyongera mu bukungu bwa mbere muri iki cyumweru.',
                'url': f'https://example.com/rwanda-{current_date}-6',
                'url_to_image': 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                'published_at': (datetime.now() - timedelta(hours=6)).isoformat(),
                'content': 'U Rwanda rwongeye kwerekana iterambere rirambye mu bukungu, hirya no hino mu gihugu.',
                'category': 'General',
                'source': 'IGIHE',
                'author': 'Umutangazamakuru',
                'language': 'rw'
            }
        ]
        
        for article_data in fallback_articles:
            try:
                # Check if already exists (by URL)
                cursor.execute('SELECT id FROM articles WHERE url = ?', (article_data['url'],))
                if cursor.fetchone():
                    continue
                
                # Get or create category
                category_name = article_data['category']
                cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
                category = cursor.fetchone()
                
                if not category:
                    cursor.execute(
                        'INSERT INTO categories (name, description) VALUES (?, ?)',
                        (category_name, f'{category_name} news')
                    )
                    category_id = cursor.lastrowid
                else:
                    category_id = category[0]
                
                # Save article
                cursor.execute('''
                    INSERT INTO articles (
                        title, description, url, url_to_image, published_at,
                        content, full_content, category_id, source, author, language,
                        is_approved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data['title'],
                    article_data['description'],
                    article_data['url'],
                    article_data['url_to_image'],
                    article_data['published_at'],
                    article_data['content'],
                    article_data['content'],
                    category_id,
                    article_data['source'],
                    article_data['author'],
                    article_data['language'],
                    0  # is_approved = False by default
                ))
                
                saved_count += 1
                logger.info(f"Added fallback article: {article_data['title']}")
                
            except Exception as e:
                logger.error(f"Error adding fallback article: {e}")
                continue
        
        conn.commit()
        conn.close()
        return saved_count
    
    def _parse_date(self, entry):
        """Parse date from entry."""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except:
            pass
        return datetime.now()
    
    def _extract_image_url(self, entry, description: str):
        """Extract image URL from entry."""
        try:
            if hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if media.get('type', '').startswith('image/'):
                        url = media.get('url')
                        if url and url.startswith('http'):
                            return url
            
            if hasattr(entry, 'media_thumbnail'):
                for thumb in entry.media_thumbnail:
                    url = thumb.get('url')
                    if url and url.startswith('http'):
                        return url
                        
            if description:
                img_match = re.search(r'<img[^>]+src="([^">]+)"', description)
                if img_match:
                    url = img_match.group(1)
                    if url and url.startswith('http'):
                        return url
        
        except Exception as e:
            logger.debug(f"Error extracting image: {e}")
        
        # Return Unsplash fallback
        categories = ['technology', 'business', 'world', 'health', 'sports', 'nature']
        category = random.choice(categories)
        unsplash_id = random.randint(1000000000, 9999999999)
        return f'https://images.unsplash.com/photo-{unsplash_id}?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'

# ==================== ENHANCED CONTENT ANALYZER ====================

class ContentAnalyzer:
    """Generate article-specific previews through content analysis."""
    
    @staticmethod
    def generate_preview(title: str, description: str, full_content: str = "", 
                        category: str = "General", source: str = "", 
                        published_date: str = None, url: str = "", author: str = "") -> str:
        """Generate article-specific preview by analyzing content."""
        
        # Clean and prepare text
        clean_desc = ContentAnalyzer._clean_text(description)
        clean_title = ContentAnalyzer._clean_text(title)
        
        # USE FULL CONTENT for analysis
        content_for_analysis = ContentAnalyzer._clean_text(full_content) if full_content and len(full_content) > len(clean_desc) else clean_desc
        
        # Analyze content for key information
        analysis = ContentAnalyzer._analyze_content(
            title=clean_title,
            description=clean_desc,
            content=content_for_analysis,
            category=category,
            source=source
        )
        
        # Build the preview
        return ContentAnalyzer._build_preview(
            title=clean_title,
            description=clean_desc,
            category=category,
            source=source,
            date=ContentAnalyzer._format_date(published_date),
            url=url,
            author=author,
            analysis=analysis
        )
    
    @staticmethod
    def _analyze_content(title: str, description: str, content: str, 
                         category: str, source: str) -> Dict:
        """Analyze article content to extract specific information."""
        
        # Use full content for better analysis
        full_text = f"{title}. {content}" if content else f"{title}. {description}"
        text_lower = full_text.lower()
        
        analysis = {
            'key_points': [],
            'entities': {'people': [], 'organizations': [], 'locations': []},
            'context': '',
            'significance': '',
            'article_type': 'standard'
        }
        
        # 1. Extract key sentences from FULL CONTENT
        if content:
            sentences = re.split(r'(?<=[.!?])\s+', content)
            if len(sentences) > 1:
                # Find meaningful sentences (not too short, contain important info)
                meaningful_sentences = []
                for sentence in sentences[:8]:  # Check first 8 sentences
                    clean_sentence = sentence.strip()
                    if (len(clean_sentence) > 30 and 
                        not clean_sentence.startswith(('©', 'Read more', 'Share', 'Photo:')) and
                        any(word in clean_sentence.lower() for word in ['said', 'announced', 'according', 'reported', 
                                                                      'confirmed', 'revealed', 'found', 'discovered',
                                                                      'explained', 'added', 'noted'])):
                        meaningful_sentences.append(clean_sentence)
                
                # If no indicator sentences, take first 3 meaningful ones
                if not meaningful_sentences:
                    meaningful_sentences = [s.strip() for s in sentences[:4] if len(s.strip()) > 25]
                
                analysis['key_points'] = meaningful_sentences[:3]
        else:
            # Fallback to description
            sentences = re.split(r'(?<=[.!?])\s+', description)
            if sentences:
                analysis['key_points'] = [s.strip() for s in sentences[:min(2, len(sentences))] if len(s) > 20]
        
        # 2. Enhanced entity extraction
        text_for_entity = title + " " + (content[:1000] if content else description)
        
        # Extract organizations with better patterns
        org_patterns = [
            # Major tech companies
            r'\b(?:Amazon|Google|Microsoft|Apple|Facebook|Meta|Twitter|X|Netflix|Tesla|SpaceX)\b',
            # Sports teams
            r'\b(?:Arsenal|Chelsea|Manchester United|Man Utd|Man City|Liverpool|Real Madrid|Barcelona)\b',
            # Media organizations
            r'\b(?:BBC|CNN|Reuters|AP|Al Jazeera|The Guardian|New York Times|Wall Street Journal)\b',
            # Government/International
            r'\b(?:UN|United Nations|WHO|World Health Organization|EU|European Union|NATO)\b',
            # Companies with Corp/Inc
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Corp|Inc|Ltd|Group|Company|PLC|SA|AG))\b',
            # Government bodies
            r'\b(?:The\s+)?[A-Z][a-z]+\s+(?:Government|Administration|Ministry|Department|Agency|Commission)\b'
        ]
        
        organizations_found = set()
        for pattern in org_patterns:
            for match in re.finditer(pattern, text_for_entity, re.IGNORECASE):
                org = match.group()
                # Clean up common variations
                if 'Man Utd' in org:
                    org = 'Manchester United'
                elif 'BBC' in org and 'Sports' not in org and 'News' not in org:
                    org = 'BBC'
                organizations_found.add(org)
        
        analysis['entities']['organizations'] = list(organizations_found)[:8]
        
        # Extract people (more comprehensive patterns)
        people_patterns = [
            r'\b(?:President|Prime Minister|Minister|CEO|Director|Professor|Dr\.|Mr\.|Ms\.)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:said|announced|confirmed|added|explained|noted)\b'
        ]
        
        people_found = set()
        for pattern in people_patterns:
            for match in re.finditer(pattern, text_for_entity):
                person = match.group(1) if len(match.groups()) > 0 else match.group()
                people_found.add(person)
        
        analysis['entities']['people'] = list(people_found)[:5]
        
        # Extract locations
        common_locations = [
            'Rwanda', 'Uganda', 'Kenya', 'Tanzania', 'South Africa', 'Nigeria',
            'USA', 'United States', 'UK', 'United Kingdom', 'China', 'India',
            'London', 'Washington', 'New York', 'Paris', 'Tokyo', 'Berlin',
            'Kigali', 'Nairobi', 'Kampala', 'Dodoma', 'Cairo', 'Lagos'
        ]
        
        locations_found = set()
        for location in common_locations:
            if location.lower() in text_lower:
                locations_found.add(location)
        
        analysis['entities']['locations'] = list(locations_found)[:5]
        
        # 3. Enhanced article type detection
        if any(word in text_lower for word in ['apologiz', 'sorry', 'regret', 'mistake', 'error', 'correction']):
            analysis['article_type'] = 'correction'
        elif any(word in text_lower for word in ['breakthrough', 'discovered', 'found', 'new study', 'research shows', 'scientists found']):
            analysis['article_type'] = 'discovery'
        elif any(word in text_lower for word in ['champions league', 'premier league', 'world cup', 'tournament', 'match', 'game']):
            analysis['article_type'] = 'sports_event'
        elif any(word in text_lower for word in ['crisis', 'emergency', 'disaster', 'outbreak', 'attack', 'conflict']):
            analysis['article_type'] = 'crisis'
        elif any(word in text_lower for word in ['election', 'vote', 'parliament', 'senate', 'government']):
            analysis['article_type'] = 'politics'
        
        # 4. Generate specific context
        analysis['context'] = ContentAnalyzer._generate_context(
            category, analysis['entities'], source, text_lower, analysis['article_type'])
        analysis['significance'] = ContentAnalyzer._generate_significance(
            category, analysis['article_type'], analysis['entities'], text_lower)
        
        return analysis
    
    @staticmethod
    def _generate_context(category: str, entities: Dict, source: str, text_lower: str, article_type: str) -> str:
        """Generate specific context based on analysis."""
        
        # Sports-specific context
        if category == 'Sports':
            if 'champions league' in text_lower:
                return "Covers UEFA Champions League developments, team performances, and match analysis."
            elif any(team in entities['organizations'] for team in ['Arsenal', 'Chelsea', 'Manchester United']):
                return "Focuses on English Premier League football, team strategies, and player performances."
            else:
                return "Reports on sports events, team performances, and athletic competitions."
        
        # Rwanda-specific
        if any('rwanda' in loc.lower() for loc in entities['locations']):
            if category == 'Business':
                return "Covers economic developments, business growth, and investment opportunities in Rwanda."
            elif category == 'General':
                return "Reports on news and current events from Rwanda and the East African region."
            else:
                return f"Discusses {category.lower()} developments and their impact in Rwanda."
        
        # Tech-specific
        if category == 'Technology':
            if 'Amazon' in entities['organizations']:
                return "Examines Amazon's technology services, e-commerce developments, or cloud computing innovations."
            elif 'Google' in entities['organizations']:
                return "Focuses on Google's products, search technology, AI research, or digital services."
            elif 'Microsoft' in entities['organizations']:
                return "Covers Microsoft's software, cloud services, or enterprise technology solutions."
            else:
                return "Discusses technology innovation, digital trends, and industry developments."
        
        # Article type specific context
        if article_type == 'sports_event':
            return "Provides coverage of competitive sports events, match analysis, and team performances."
        elif article_type == 'discovery':
            return "Reports on new scientific findings, research outcomes, or technological discoveries."
        elif article_type == 'correction':
            return "Addresses corrections, clarifications, or apologies related to previous reporting."
        
        # Default category-based context
        context_map = {
            'Business': "Covers economic trends, market movements, corporate news, and financial developments.",
            'Health': "Reports on medical research, healthcare developments, public health information, and wellness.",
            'World': "Provides international news coverage, global events, and cross-border developments.",
            'Politics': "Covers political developments, government policies, elections, and legislative actions.",
            'Entertainment': "Discusses film, television, music, arts, and celebrity news and events.",
            'Science': "Reports on scientific discoveries, research findings, and academic developments."
        }
        
        return context_map.get(category, 
            f"Provides coverage of {category.lower()} news and current developments.")
    
    @staticmethod
    def _generate_significance(category: str, article_type: str, entities: Dict, text_lower: str) -> str:
        """Generate significance statement."""
        
        # Article type specific significance
        if article_type == 'correction':
            return "Demonstrates journalistic accountability and the importance of accurate reporting."
        elif article_type == 'discovery':
            return "Represents advancements in knowledge with potential real-world applications and impact."
        elif article_type == 'sports_event':
            if 'champions league' in text_lower:
                return "Important for football fans tracking European club competitions and team progress."
            else:
                return "Reflects cultural interests, competitive achievements, and sports entertainment value."
        elif article_type == 'crisis':
            return "Critical information for public awareness, safety measures, and emergency response."
        
        # Category-based significance
        significance_map = {
            'Technology': "Tech developments influence business, society, daily life, and future innovation globally.",
            'Business': "Economic news helps understand market conditions, investment opportunities, and financial trends.",
            'Health': "Health information is vital for personal wellbeing, medical decisions, and public health awareness.",
            'World': "International news provides insights into global relations, cultural understanding, and world events.",
            'Science': "Scientific advances drive innovation, address global challenges, and expand human knowledge.",
            'Sports': "Sports news reflects cultural interests, competitive entertainment, and athletic achievements.",
            'Politics': "Political developments shape governance, policy decisions, and societal direction."
        }
        
        return significance_map.get(category, 
            "Provides valuable information for understanding current events, trends, and developments.")
    
    @staticmethod
    def _build_preview(title: str, description: str, category: str,
                      source: str, date: str, url: str, author: str,
                      analysis: Dict) -> str:
        """Build the enhanced preview HTML."""
        
        color = ContentAnalyzer._get_category_color(category)
        
        html_parts = []
        
        # Header
        html_parts.append(f'''
<div class="news-preview" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <div style="border-left: 4px solid {color}; padding-left: 16px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                {category}
            </span>
            <span style="color: #6b7280; font-size: 13px;">
                {source} • {date if date else "Recent"}
            </span>
            {f'<span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 500;">{analysis["article_type"].upper().replace("_", " ")}</span>' if analysis["article_type"] != "standard" else ''}
        </div>
        <h2 style="margin: 0 0 12px 0; color: #111827; font-size: 22px; line-height: 1.3;">
            {html.escape(title)}
        </h2>
        {f'<div style="color: #6b7280; font-size: 14px; margin-bottom: 8px;">By {html.escape(author)}</div>' if author and author != "Unknown" else ''}
    </div>
''')
        
        # Article Summary
        html_parts.append(f'''
    <div style="margin-bottom: 24px; background-color: #f9fafb; padding: 20px; border-radius: 8px;">
        <h3 style="margin: 0 0 12px 0; color: #374151; font-size: 16px; font-weight: 600;">
            Article Summary
        </h3>
        <p style="margin: 0; color: #4b5563; line-height: 1.6;">
            {html.escape(description) if description else "Summary not available."}
        </p>
    </div>
''')
        
        # Key Entities (if found)
        has_entities = any(analysis['entities'].values())
        if has_entities:
            html_parts.append('''
    <div style="margin-bottom: 24px;">
        <h3 style="margin: 0 0 12px 0; color: #111827; font-size: 18px; font-weight: 600;">
            Key Entities Mentioned
        </h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
''')
            
            entity_types = [
                ('organizations', '🏢 Organizations', '#dbeafe', '#1e40af'),
                ('people', '👥 People', '#fce7f3', '#be185d'),
                ('locations', '📍 Locations', '#dcfce7', '#166534')
            ]
            
            for entity_key, label, bg_color, text_color in entity_types:
                if analysis['entities'][entity_key]:
                    entities_html = ', '.join([
                        f'<span style="background-color: {bg_color}; color: {text_color}; padding: 2px 8px; border-radius: 6px; font-size: 12px; display: inline-block; margin: 2px;">{html.escape(e)}</span>'
                        for e in analysis['entities'][entity_key]
                    ])
                    
                    html_parts.append(f'''
            <div style="background-color: #f8fafc; padding: 16px; border-radius: 8px;">
                <div style="font-weight: 600; color: #475569; font-size: 13px; margin-bottom: 8px;">{label}</div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    {entities_html}
                </div>
            </div>
''')
            
            html_parts.append('''
        </div>
    </div>
''')
        
        # Key Points (only show if we have meaningful points)
        if analysis['key_points'] and any(len(p) > 25 for p in analysis['key_points']):
            html_parts.append('''
    <div style="margin-bottom: 24px;">
        <h3 style="margin: 0 0 12px 0; color: #111827; font-size: 18px; font-weight: 600;">
            Key Points
        </h3>
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px;">
            <ul style="margin: 0; padding-left: 20px;">
''')
            
            for point in analysis['key_points']:
                if len(point) > 25:  # Only show meaningful points
                    html_parts.append(f'''
                <li style="margin-bottom: 10px; color: #0369a1; line-height: 1.5; padding-left: 4px;">
                    {html.escape(point)}
                </li>
''')
            
            html_parts.append('''
            </ul>
        </div>
    </div>
''')
        
        # Context & Significance
        html_parts.append(f'''
    <div style="margin-bottom: 24px;">
        <h3 style="margin: 0 0 12px 0; color: #111827; font-size: 18px; font-weight: 600;">
            Analysis
        </h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
            <div style="background-color: #fefce8; padding: 16px; border-radius: 8px; border-left: 3px solid #f59e0b;">
                <h4 style="margin: 0 0 8px 0; color: #92400e; font-size: 14px; font-weight: 600;">
                    📋 Context
                </h4>
                <p style="margin: 0; color: #78350f; line-height: 1.5; font-size: 14px;">
                    {html.escape(analysis['context'])}
                </p>
            </div>
            <div style="background-color: #f0f9ff; padding: 16px; border-radius: 8px; border-left: 3px solid #0ea5e9;">
                <h4 style="margin: 0 0 8px 0; color: #0369a1; font-size: 14px; font-weight: 600;">
                    🎯 Significance
                </h4>
                <p style="margin: 0; color: #0369a1; line-height: 1.5; font-size: 14px;">
                    {html.escape(analysis['significance'])}
                </p>
            </div>
        </div>
    </div>
''')
        
        # Read More
        html_parts.append(f'''
    <div style="margin-top: 32px; text-align: center; padding: 20px; background: linear-gradient(135deg, {color}10 0%, {color}05 100%); border-radius: 12px;">
        <h3 style="margin: 0 0 16px 0; color: #111827; font-size: 18px; font-weight: 600;">
            Read the Full Story
        </h3>
        <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 15px;">
            This enhanced preview analyzes key information from the article. The complete story contains additional details and full coverage.
        </p>
        <a href="{html.escape(url)}" target="_blank" style="display: inline-block; background-color: {color}; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px;">
            📖 Read Full Article at {source}
        </a>
        <div style="margin-top: 16px; font-size: 13px; color: #6b7280;">
            <svg style="width: 14px; height: 14px; vertical-align: middle; margin-right: 6px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Enhanced preview with full content analysis • Globe News v6.1
        </div>
    </div>
</div>
''')
        
        return '\n'.join(html_parts)
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text of HTML and extra whitespace."""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = html.unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    @staticmethod
    def _get_category_color(category: str) -> str:
        """Get color for category."""
        colors = {
            'World': '#3b82f6',
            'Technology': '#8b5cf6',
            'Business': '#10b981',
            'Science': '#06b6d4',
            'Health': '#ec4899',
            'Sports': '#f97316',
            'Entertainment': '#ef4444',
            'Politics': '#6b7280',
            'General': '#6366f1'
        }
        return colors.get(category, '#6366f1')
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format date string nicely."""
        if not date_str:
            return ""
        
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return date_str
            
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes}m ago"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours}h ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days}d ago"
            else:
                return dt.strftime("%b %d, %Y")
                
        except Exception:
            return date_str

# ==================== BACKGROUND TASKS ====================

async def background_fetcher():
    """Background task to fetch news periodically."""
    logger.info("Starting background news fetcher...")
    
    await asyncio.sleep(10)
    
    while True:
        try:
            fetcher = NewsFetcher()
            count = await fetcher.fetch_all_news()
            
            if count > 0:
                logger.info(f"Background fetch: Saved {count} new articles")
            else:
                logger.info("No new articles fetched in this cycle")
            
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in background fetcher: {e}")
            await asyncio.sleep(600)

# ==================== FASTAPI APP ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting Globe News API...")
    
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Check initial article count
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM articles')
        count = cursor.fetchone()[0]
        conn.close()
        
        logger.info(f"Initial database has {count} articles")
        
        if count == 0:
            logger.info("Database is empty, adding initial articles...")
            fetcher = NewsFetcher()
            initial_count = await fetcher.add_fallback_articles()
            logger.info(f"Added {initial_count} initial articles")
    except Exception as e:
        logger.error(f"Error checking database: {e}")
    
    # Start background tasks
    task = asyncio.create_task(background_fetcher())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Globe News API...")
    task.cancel()

# Create FastAPI app
app = FastAPI(
    title="Globe News API",
    description="Global news aggregator with smart content previews and full article extraction",
    version="6.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ADMIN ROUTES - MOVED HERE (FIXED)
app.include_router(admin.router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint with system info."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE language = "en"')
        english = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE language = "rw"')
        kinyarwanda = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE LENGTH(full_content) > LENGTH(content) + 100')
        full_content_extracted = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM articles 
            GROUP BY source 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        sources = cursor.fetchall()
        
        conn.close()
        
        return {
            "message": "Globe News API",
            "version": "6.1.0",
            "status": "running",
            "docs": "/docs",
            "statistics": {
                "total_articles": total,
                "english_articles": english,
                "kinyarwanda_articles": kinyarwanda,
                "full_content_extracted": full_content_extracted,
                "content_extraction_rate": f"{(full_content_extracted/total*100):.1f}%" if total > 0 else "0%"
            },
            "top_sources": [dict(s) for s in sources],
            "features": [
                "Real-time RSS news fetching",
                "Full article content extraction",
                "Smart content preview generation",
                "Multi-language support (English & Kinyarwanda)",
                "Automatic hourly updates",
                "Article-specific context analysis",
                "Admin approval workflow for AdSense compliance"
            ],
            "content_extraction": {
                "library": "readability-lxml (if available)",
                "fallback": "HTML pattern matching",
                "max_length": "15000 characters"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return {
            "message": "Globe News API",
            "version": "6.1.0",
            "status": "running",
            "docs": "/docs"
        }

@app.get("/api/v1/health/status")
async def health_status():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Globe News API",
        "version": "6.1.0",
        "timestamp": datetime.now().isoformat(),
        "content_extraction": "readability-lxml" if Document else "fallback only"
    }

@app.get("/api/v1/articles")
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    language: str = Query(None),
    search: str = Query(None)
):
    """Get articles with filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query - only show approved articles
        query = '''
            SELECT a.*, c.name as category_name 
            FROM articles a 
            LEFT JOIN categories c ON a.category_id = c.id 
            WHERE a.is_approved = 1
        '''
        params = []
        
        if category:
            query += ' AND c.name = ?'
            params.append(category)
        
        if language and language != 'all':
            query += ' AND a.language = ?'
            params.append(language)
        
        if search:
            query += ' AND (a.title LIKE ? OR a.description LIKE ? OR a.full_content LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        # Order and paginate
        query += ' ORDER BY a.published_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        
        # Get total count
        count_query = 'SELECT COUNT(*) FROM articles a LEFT JOIN categories c ON a.category_id = c.id WHERE a.is_approved = 1'
        count_params = []
        
        if category:
            count_query += ' AND c.name = ?'
            count_params.append(category)
        
        if language and language != 'all':
            count_query += ' AND a.language = ?'
            count_params.append(language)
        
        if search:
            count_query += ' AND (a.title LIKE ? OR a.description LIKE ? OR a.full_content LIKE ?)'
            search_term = f'%{search}%'
            count_params.extend([search_term, search_term, search_term])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        # Convert to dict
        result = []
        for article in articles:
            article_dict = dict(article)
            article_dict.setdefault('category_name', 'General')
            article_dict.setdefault('language', 'en')
            article_dict.setdefault('source', 'Unknown')
            article_dict.setdefault('author', 'Unknown')
            article_dict.setdefault('preview_content', None)
            article_dict.setdefault('full_content', None)
            
            # Add content length info
            if article_dict.get('full_content'):
                article_dict['content_length'] = len(article_dict['full_content'])
                article_dict['has_full_content'] = len(article_dict['full_content']) > len(article_dict.get('content', '')) + 100
            else:
                article_dict['content_length'] = len(article_dict.get('content', ''))
                article_dict['has_full_content'] = False
            
            result.append(article_dict)
        
        conn.close()
        
        return {
            "articles": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/articles/{article_id}")
async def get_article(article_id: int):
    """Get single article by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.name as category_name 
            FROM articles a 
            LEFT JOIN categories c ON a.category_id = c.id 
            WHERE a.id = ? AND a.is_approved = 1
        ''', (article_id,))
        
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Convert to dictionary
        article_dict = dict(article)
        article_dict.setdefault('category_name', 'General')
        article_dict.setdefault('language', 'en')
        article_dict.setdefault('source', 'Unknown')
        article_dict.setdefault('author', 'Unknown')
        article_dict.setdefault('preview_content', None)
        article_dict.setdefault('full_content', None)
        
        # Add content info
        if article_dict.get('full_content'):
            article_dict['has_full_content'] = True
            article_dict['content_length'] = len(article_dict['full_content'])
        else:
            article_dict['has_full_content'] = False
            article_dict['content_length'] = len(article_dict.get('content', ''))
        
        # Get related articles
        language = article_dict.get('language', 'en')
        category_id = article_dict.get('category_id', 1)
        
        cursor.execute('''
            SELECT a.*, c.name as category_name 
            FROM articles a 
            LEFT JOIN categories c ON a.category_id = c.id 
            WHERE a.category_id = ? AND a.id != ? AND a.language = ? AND a.is_approved = 1
            ORDER BY a.published_at DESC 
            LIMIT 5
        ''', (category_id, article_id, language))
        
        related = cursor.fetchall()
        
        # Convert related articles to dict
        related_list = []
        for rel in related:
            rel_dict = dict(rel)
            rel_dict.setdefault('category_name', 'General')
            rel_dict.setdefault('language', 'en')
            related_list.append(rel_dict)
        
        article_dict['related_articles'] = related_list
        
        conn.close()
        return article_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching article: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/articles/breaking/")
async def get_breaking_articles(limit: int = Query(20, ge=1, le=100)):
    """Get breaking news (last 24 hours)."""
    try:
        time_threshold = (datetime.now() - timedelta(hours=24)).isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.name as category_name 
            FROM articles a 
            LEFT JOIN categories c ON a.category_id = c.id 
            WHERE a.published_at > ? AND a.is_approved = 1
            ORDER BY a.published_at DESC 
            LIMIT ?
        ''', (time_threshold, limit))
        
        articles = cursor.fetchall()
        conn.close()
        
        result = []
        for article in articles:
            article_dict = dict(article)
            article_dict.setdefault('category_name', 'General')
            article_dict.setdefault('language', 'en')
            article_dict['is_breaking'] = True
            
            if article_dict.get('full_content'):
                article_dict['has_full_content'] = True
            
            result.append(article_dict)
        
        return {
            "articles": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error fetching breaking articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/categories")
async def get_categories():
    """Get all categories."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        
        return [dict(c) for c in categories]
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return []

@app.get("/api/v1/fetcher/stats")
async def get_fetcher_stats():
    """Get system statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE language = "en"')
        english = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE language = "rw"')
        kinyarwanda = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE LENGTH(full_content) > LENGTH(content) + 100')
        full_content_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE is_approved = 0')
        pending_approval = cursor.fetchone()[0]
        
        cursor.execute('SELECT MAX(published_at) FROM articles')
        latest_date_result = cursor.fetchone()[0]
        latest_date = latest_date_result if latest_date_result else datetime.now().isoformat()
        
        conn.close()
        
        return {
            "total_articles": total,
            "english_articles": english,
            "kinyarwanda_articles": kinyarwanda,
            "full_content_extracted": full_content_count,
            "extraction_rate": f"{(full_content_count/total*100):.1f}%" if total > 0 else "0%",
            "pending_approval": pending_approval,
            "latest_article_date": latest_date,
            "configured_feeds": len(RSS_FEEDS),
            "content_extraction_enabled": Document is not None,
            "admin_workflow": "Articles require approval before public viewing"
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "total_articles": 0,
            "english_articles": 0,
            "kinyarwanda_articles": 0,
            "full_content_extracted": 0,
            "extraction_rate": "0%",
            "pending_approval": 0,
            "latest_article_date": None,
            "configured_feeds": len(RSS_FEEDS),
            "content_extraction_enabled": Document is not None
        }

@app.post("/api/v1/fetcher/fetch-now")
async def fetch_now(background_tasks: BackgroundTasks):
    """Trigger immediate news fetching."""
    async def fetch_task():
        try:
            fetcher = NewsFetcher()
            count = await fetcher.fetch_all_news()
            return count
        except Exception as e:
            logger.error(f"Error in manual fetch: {e}")
            return 0
    
    background_tasks.add_task(fetch_task)
    
    return {
        "message": "News fetch started in background",
        "status": "processing",
        "note": "New articles will require admin approval before appearing on site"
    }

# ==================== CONTENT PREVIEW ENDPOINTS ====================

@app.get("/api/v1/preview/articles/{article_id}")
async def get_article_preview(article_id: int):
    """Get content preview for an article."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.name as category_name 
            FROM articles a 
            LEFT JOIN categories c ON a.category_id = c.id 
            WHERE a.id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")
        
        article_dict = dict(article)
        
        # Check if preview already exists
        if article_dict.get('preview_content'):
            conn.close()
            return {
                "article_id": article_id,
                "preview": article_dict['preview_content'],
                "has_preview": True,
                "generated": False,
                "has_full_content": bool(article_dict.get('full_content'))
            }
        
        # Generate smart preview WITH FULL CONTENT
        preview = ContentAnalyzer.generate_preview(
            title=article_dict.get('title', ''),
            description=article_dict.get('description', ''),
            full_content=article_dict.get('full_content', article_dict.get('content', '')),
            category=article_dict.get('category_name', 'General'),
            source=article_dict.get('source', 'Unknown'),
            published_date=article_dict.get('published_at', ''),
            url=article_dict.get('url', ''),
            author=article_dict.get('author', '')
        )
        
        # Save preview
        cursor.execute(
            'UPDATE articles SET preview_content = ? WHERE id = ?',
            (preview, article_id)
        )
        conn.commit()
        conn.close()
        
        return {
            "article_id": article_id,
            "preview": preview,
            "has_preview": True,
            "generated": True,
            "has_full_content": bool(article_dict.get('full_content'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/preview/articles/{article_id}/generate")
async def generate_preview(article_id: int):
    """Generate content preview for an article."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.name as category_name 
            FROM articles a 
            LEFT JOIN categories c ON a.category_id = c.id 
            WHERE a.id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")
        
        article_dict = dict(article)
        
        # Generate smart preview WITH FULL CONTENT
        preview = ContentAnalyzer.generate_preview(
            title=article_dict.get('title', ''),
            description=article_dict.get('description', ''),
            full_content=article_dict.get('full_content', article_dict.get('content', '')),
            category=article_dict.get('category_name', 'General'),
            source=article_dict.get('source', 'Unknown'),
            published_date=article_dict.get('published_at', ''),
            url=article_dict.get('url', ''),
            author=article_dict.get('author', '')
        )
        
        # Save preview
        cursor.execute(
            'UPDATE articles SET preview_content = ? WHERE id = ?',
            (preview, article_id)
        )
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "article_id": article_id,
            "preview": preview,
            "message": "Preview generated successfully",
            "used_full_content": bool(article_dict.get('full_content'))
        }
        
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return {
            "success": False,
            "article_id": article_id,
            "preview": f"Error generating preview: {str(e)}",
            "message": "Failed to generate preview"
        }

# ✅ NEW: Content extraction debug endpoint
@app.get("/api/v1/debug/extract-test")
async def debug_extract_test(url: str = Query(..., description="URL to test content extraction")):
    """Test content extraction on a specific URL."""
    try:
        fetcher = NewsFetcher()
        
        # Extract content
        start_time = datetime.now()
        content = await fetcher.extract_full_content(url, "Test description", "Test Source")
        extraction_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "url": url,
            "extraction_time_seconds": extraction_time,
            "content_length": len(content),
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "readability_available": Document is not None,
            "success": len(content) > 100
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    init_db()
    print("✅ Database initialized")

# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
