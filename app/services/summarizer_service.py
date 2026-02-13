from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import Dict, List, Optional
from ..ai.summarizer import get_summarizer
from ..models.minimal_models import Article

logger = logging.getLogger(__name__)

class SummarizerService:
    """Service layer for AI summarization operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.summarizer = get_summarizer()
        
    def generate_article_summary(self, article_id: int) -> Optional[Dict]:
        """
        Generate AI summary for a specific article
        
        Args:
            article_id: ID of the article to summarize
            
        Returns:
            Dictionary with summary paragraphs or None if failed
        """
        try:
            # Get article from database
            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                logger.error(f"Article {article_id} not found")
                return None
            
            # Check if already summarized
            if article.ai_summary_generated:
                logger.info(f"Article {article_id} already has AI summary")
                return self._format_existing_summary(article)
            
            # Prepare text for summarization
            article_text = article.full_content or article.summary or ""
            if not article_text:
                logger.error(f"Article {article_id} has no content to summarize")
                return None
            
            # Generate summary
            logger.info(f"Generating AI summary for article {article_id}")
            summaries = self.summarizer.generate_six_paragraph_summary(
                article_text, 
                article.title
            )
            
            # Update article with generated summaries
            article.ai_summary_1 = summaries.get("ai_summary_1")
            article.ai_summary_2 = summaries.get("ai_summary_2")
            article.ai_summary_3 = summaries.get("ai_summary_3")
            article.ai_summary_4 = summaries.get("ai_summary_4")
            article.ai_summary_5 = summaries.get("ai_summary_5")
            article.ai_summary_6 = summaries.get("ai_summary_6")
            article.ai_summary_generated = True
            article.ai_summary_generated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Successfully generated and saved AI summary for article {article_id}")
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error generating summary for article {article_id}: {str(e)}")
            self.db.rollback()
            return None
    
    def batch_generate_summaries(self, article_ids: List[int]) -> Dict[int, bool]:
        """
        Generate summaries for multiple articles
        
        Args:
            article_ids: List of article IDs to summarize
            
        Returns:
            Dictionary mapping article_id -> success status
        """
        results = {}
        
        for article_id in article_ids:
            try:
                summary = self.generate_article_summary(article_id)
                results[article_id] = summary is not None
                
                # Small delay to avoid overwhelming
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in batch summary for article {article_id}: {str(e)}")
                results[article_id] = False
        
        return results
    
    def get_article_summary(self, article_id: int) -> Optional[Dict]:
        """
        Get AI summary for an article (generate if not exists)
        
        Args:
            article_id: ID of the article
            
        Returns:
            Dictionary with summary paragraphs or None if failed
        """
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return None
        
        if not article.ai_summary_generated:
            return self.generate_article_summary(article_id)
        
        return self._format_existing_summary(article)
    
    def _format_existing_summary(self, article: Article) -> Dict:
        """Format existing summary from article object"""
        return {
            "ai_summary_1": article.ai_summary_1,
            "ai_summary_2": article.ai_summary_2,
            "ai_summary_3": article.ai_summary_3,
            "ai_summary_4": article.ai_summary_4,
            "ai_summary_5": article.ai_summary_5,
            "ai_summary_6": article.ai_summary_6,
            "ai_summary_generated": article.ai_summary_generated,
            "ai_summary_generated_at": article.ai_summary_generated_at.isoformat() if article.ai_summary_generated_at else None
        }
    
    def get_unsummarized_articles(self, limit: int = 10) -> List[Article]:
        """
        Get articles that don't have AI summaries yet
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of Article objects
        """
        return self.db.query(Article)\
            .filter(
                (Article.ai_summary_generated == False) | 
                (Article.ai_summary_generated.is_(None))
            )\
            .filter(Article.full_content.isnot(None))\
            .limit(limit)\
            .all()