# Export the models with proper names - REMOVED Source
from app.models.minimal_models import Article, Category

# Keep backward compatibility
NewsArticle = Article

# Also export the old names for compatibility
MinimalArticle = Article
MinimalCategory = Category

__all__ = [
    'Article',
    'Category',
    'NewsArticle',
    'MinimalArticle',
    'MinimalCategory'
]
