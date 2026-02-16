# Export the models with proper names - FIXED IMPORT PATH
from app.models.minimal_models import Article, Category, User, Source

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
    'User',
    'NewsArticle',
    'NewsSource',
    'MinimalArticle',
    'MinimalSource',
    'MinimalCategory'
]
