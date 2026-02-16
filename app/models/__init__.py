# Export the models with proper names
from app.minimal_models import Article, Category, User, Source

# Keep backward compatibility
NewsArticle = Article
NewsSource = Source
Category = Category

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
