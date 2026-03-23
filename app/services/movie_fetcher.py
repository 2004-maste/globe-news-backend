"""
Movie/Entertainment Service - TMDB API Integration
Fetches trending movies, TV shows, and streaming information
"""

import os
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
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
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def fetch_trending(self, media_type: str = 'all', time_window: str = 'day') -> List[Dict]:
        """
        Fetch trending movies or TV shows
        media_type: 'all', 'movie', 'tv'
        time_window: 'day' or 'week'
        """
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
                    for item in results[:20]:  # Limit to 20 trending items
                        processed.append(await self._process_movie_item(item))
                    
                    logger.info(f"Fetched {len(processed)} trending {media_type} items")
                    return processed
                    
        except Exception as e:
            logger.error(f"Error fetching trending: {e}")
            return []
    
    async def fetch_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Fetch detailed movie information including watch providers"""
        if not self.api_key:
            return None
            
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Fetch movie details
                url = f"{TMDB_BASE_URL}/movie/{movie_id}"
                params = {'api_key': self.api_key, 'append_to_response': 'watch/providers,credits,similar'}
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    return await self._process_movie_details(data)
                    
        except Exception as e:
            logger.error(f"Error fetching movie {movie_id}: {e}")
            return None
    
    async def fetch_tv_details(self, tv_id: int) -> Optional[Dict]:
        """Fetch detailed TV show information"""
        if not self.api_key:
            return None
            
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{TMDB_BASE_URL}/tv/{tv_id}"
                params = {'api_key': self.api_key, 'append_to_response': 'watch/providers,credits,similar'}
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    return await self._process_tv_details(data)
                    
        except Exception as e:
            logger.error(f"Error fetching TV show {tv_id}: {e}")
            return None
    
    async def search_movies(self, query: str, page: int = 1) -> List[Dict]:
        """Search for movies by title"""
        if not self.api_key:
            return []
            
        try:
            url = f"{TMDB_BASE_URL}/search/movie"
            params = {'api_key': self.api_key, 'query': query, 'page': page}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    results = data.get('results', [])
                    
                    processed = []
                    for item in results[:10]:
                        processed.append(await self._process_movie_item(item))
                    
                    return processed
                    
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            return []
    
    async def _process_movie_item(self, item: Dict) -> Dict:
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
            'genre_ids': item.get('genre_ids', [])
        }
        
        return result
    
    async def _process_movie_details(self, data: Dict) -> Dict:
        """Process detailed movie information"""
        # Basic info
        result = await self._process_movie_item(data)
        
        # Add detailed info
        result.update({
            'tagline': data.get('tagline', ''),
            'runtime': data.get('runtime', 0),
            'budget': data.get('budget', 0),
            'revenue': data.get('revenue', 0),
            'status': data.get('status', ''),
            'homepage': data.get('homepage', ''),
            'imdb_id': data.get('imdb_id', ''),
            'genres': [g.get('name') for g in data.get('genres', [])],
            'production_companies': [c.get('name') for c in data.get('production_companies', [])],
            'production_countries': [c.get('name') for c in data.get('production_countries', [])]
        })
        
        # Cast (top 10)
        credits = data.get('credits', {})
        result['cast'] = [
            {
                'name': c.get('name'),
                'character': c.get('character'),
                'profile_path': f"{TMDB_IMAGE_BASE}/w185{c.get('profile_path')}" if c.get('profile_path') else None
            }
            for c in credits.get('cast', [])[:10]
        ]
        
        # Director
        result['director'] = None
        for crew in credits.get('crew', []):
            if crew.get('job') == 'Director':
                result['director'] = crew.get('name')
                break
        
        # Watch providers (where to stream)
        watch_providers = data.get('watch/providers', {}).get('results', {})
        
        # US providers (or fallback to first available)
        us_providers = watch_providers.get('US', {})
        
        result['streaming_info'] = {
            'flatrate': [p.get('provider_name') for p in us_providers.get('flatrate', [])],
            'rent': [p.get('provider_name') for p in us_providers.get('rent', [])],
            'buy': [p.get('provider_name') for p in us_providers.get('buy', [])],
            'link': us_providers.get('link')
        }
        
        # Similar movies
        similar = data.get('similar', {}).get('results', [])
        result['similar'] = [await self._process_movie_item(s) for s in similar[:6]]
        
        return result
    
    async def _process_tv_details(self, data: Dict) -> Dict:
        """Process detailed TV show information"""
        # Basic info (using movie processor but with TV fields)
        result = {
            'id': data.get('id'),
            'title': data.get('name'),
            'original_title': data.get('original_name'),
            'type': 'tv',
            'overview': data.get('overview', ''),
            'poster_url': f"{TMDB_IMAGE_BASE}/w500{data.get('poster_path')}" if data.get('poster_path') else None,
            'backdrop_url': f"{TMDB_IMAGE_BASE}/original{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
            'release_date': data.get('first_air_date'),
            'rating': data.get('vote_average', 0),
            'vote_count': data.get('vote_count', 0),
            'popularity': data.get('popularity', 0),
            'language': data.get('original_language', 'en'),
            'genre_ids': [g.get('id') for g in data.get('genres', [])]
        }
        
        # Add TV-specific details
        result.update({
            'tagline': data.get('tagline', ''),
            'status': data.get('status', ''),
            'homepage': data.get('homepage', ''),
            'number_of_seasons': data.get('number_of_seasons', 0),
            'number_of_episodes': data.get('number_of_episodes', 0),
            'genres': [g.get('name') for g in data.get('genres', [])],
            'networks': [n.get('name') for n in data.get('networks', [])],
            'last_air_date': data.get('last_air_date')
        })
        
        # Cast
        credits = data.get('credits', {})
        result['cast'] = [
            {
                'name': c.get('name'),
                'character': c.get('character'),
                'profile_path': f"{TMDB_IMAGE_BASE}/w185{c.get('profile_path')}" if c.get('profile_path') else None
            }
            for c in credits.get('cast', [])[:10]
        ]
        
        # Creator
        result['creator'] = None
        for crew in credits.get('crew', []):
            if crew.get('job') == 'Creator':
                result['creator'] = crew.get('name')
                break
        
        # Watch providers
        watch_providers = data.get('watch/providers', {}).get('results', {})
        us_providers = watch_providers.get('US', {})
        
        result['streaming_info'] = {
            'flatrate': [p.get('provider_name') for p in us_providers.get('flatrate', [])],
            'rent': [p.get('provider_name') for p in us_providers.get('rent', [])],
            'buy': [p.get('provider_name') for p in us_providers.get('buy', [])],
            'link': us_providers.get('link')
        }
        
        # Similar shows
        similar = data.get('similar', {}).get('results', [])
        result['similar'] = [await self._process_movie_item(s) for s in similar[:6]]
        
        return result
