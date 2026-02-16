# Export the models with proper names - REMOVED User since it doesn't exist
from app.models.minimal_models import Article, Category, Source

# Keep backward compatibility
NewsArticle = Article
NewsSource = Source

# Also export the old names for compatibility
MinimalArticle = Article
MinimalSource = Source
MinimalCategory = Category

__all__ = [
    'Article',
    'Source', 
    'Category',
    'NewsArticle',
    'NewsSource',
    'MinimalArticle',
    'MinimalSource',
    'MinimalCategory'
]
