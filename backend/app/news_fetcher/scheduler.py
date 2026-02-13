"""
Scheduler for periodic news fetching
"""
import schedule
import time
import threading
import logging
from datetime import datetime
from typing import Optional

from .fetcher_service import NewsFetcherService

logger = logging.getLogger(__name__)

class NewsScheduler:
    """Scheduler for periodic news fetching"""
    
    def __init__(self, interval_minutes: int = 30):
        self.interval = interval_minutes
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self.fetcher_service = NewsFetcherService()
        
    def fetch_job(self):
        """Job to fetch news"""
        try:
            logger.info(f"🔄 Scheduled news fetch started at {datetime.utcnow().isoformat()}")
            results = self.fetcher_service.fetch_and_store_news(max_articles=50)
            logger.info(f"✅ Scheduled fetch completed: {results['new_articles_added']} new articles")
        except Exception as e:
            logger.error(f"❌ Error in scheduled fetch: {e}")
    
    def start(self):
        """Start the scheduler in a separate thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        logger.info(f"Starting news scheduler (interval: {self.interval} minutes)")
        
        # Schedule the job
        schedule.every(self.interval).minutes.do(self.fetch_job)
        
        # Run once immediately
        self.fetch_job()
        
        # Start scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("News scheduler started successfully")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("News scheduler stopped")
    
    def run_once(self) -> dict:
        """Run fetch once manually"""
        try:
            logger.info("Manual news fetch started")
            results = self.fetcher_service.fetch_and_store_news(max_articles=100)
            logger.info(f"Manual fetch completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in manual fetch: {e}")
            return {"error": str(e)}