"""
Movie/Entertainment Service - TMDB API Integration
Fetches trending movies, TV shows, and streaming information
"""

import os
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# TMDB API Configuration
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p'


class MovieFetcher:
    """Fetch movies, TV shows, and trending content from TMDB"""
    
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def fetch_trending(self, media_type: str = 'all', time_window: str = 'day') -> List[Dict]:
        """Fetch trending movies or TV shows"""
        if not self.api_key:
            logger.error("TMDB_API_KEY not configured")
            return []
            
        try:
            url = f"{TMDB_BASE_URL}/trending/{media_type}/{time_window}"
            params = {'api_key': self.api_key}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"TMDB API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    results = data.get('results', [])
                    
                    # Process each item
                    processed = []
                    for item in results[:20]:
                        processed.append(self._process_movie_item(item))
                    
                    logger.info(f"Fetched {len(processed)} trending {media_type} items")
                    return processed
                    
        except Exception as e:
            logger.error(f"Error fetching trending: {e}")
            return []
    
    def _process_movie_item(self, item: Dict) -> Dict:
        """Process a movie/tv item from trending/search results"""
        is_movie = item.get('media_type') == 'movie' or 'release_date' in item
        is_tv = item.get('media_type') == 'tv' or 'first_air_date' in item
        
        # Build poster URL
        poster_path = item.get('poster_path')
        backdrop_path = item.get('backdrop_path')
        
        poster_url = f"{TMDB_IMAGE_BASE}/w500{poster_path}" if poster_path else None
        backdrop_url = f"{TMDB_IMAGE_BASE}/original{backdrop_path}" if backdrop_path else None
        
        # Get release date / first air date
        release_date = item.get('release_date') if is_movie else item.get('first_air_date')
        
        # Get rating
        rating = item.get('vote_average', 0)
        vote_count = item.get('vote_count', 0)
        
        # Build the result
        result = {
            'id': item.get('id'),
            'title': item.get('title') if is_movie else item.get('name'),
            'original_title': item.get('original_title') if is_movie else item.get('original_name'),
            'type': 'movie' if is_movie else ('tv' if is_tv else 'unknown'),
            'overview': item.get('overview', ''),
            'poster_url': poster_url,
            'backdrop_url': backdrop_url,
            'release_date': release_date,
            'rating': rating,
            'vote_count': vote_count,
            'popularity': item.get('popularity', 0),
            'language': item.get('original_language', 'en'),
            'genres': []
        }
        
        return result
