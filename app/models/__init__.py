# Export the models with proper names
from app.models.models import Article, Source, Category

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
