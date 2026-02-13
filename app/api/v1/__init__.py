"""
API v1 router and endpoints.
"""
from fastapi import APIRouter

# Import all endpoint routers
from app.api.v1.endpoints.articles import router as articles_router
from app.api.v1.endpoints.sources import router as sources_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()

# Include all routers
api_router.include_router(articles_router, prefix="/articles", tags=["articles"])
api_router.include_router(sources_router, prefix="/sources", tags=["sources"])
api_router.include_router(categories_router, prefix="/categories", tags=["categories"])
api_router.include_router(health_router, prefix="/health", tags=["health"])