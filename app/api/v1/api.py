"""
Main API Router
"""
from fastapi import APIRouter
from .endpoints import articles, categories, health, summarizer, fetcher

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(summarizer.router, prefix="/summarizer", tags=["summarizer"])
api_router.include_router(fetcher.router, prefix="/fetcher", tags=["fetcher"])