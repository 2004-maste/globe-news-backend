import os
import logging

logger = logging.getLogger(__name__)

# Simple settings without Pydantic
APP_NAME = "Globe News API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Global News Aggregator with AI Summarization"
DEBUG = True
DATABASE_URL = "sqlite:///./test.db"
API_PREFIX = "/api/v1"
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]

# AI settings
AI_MODEL_NAME = "facebook/bart-large-cnn"
AI_MAX_CHUNK_SIZE = 1000

# Log settings
logger.info(f"Loaded settings for {APP_NAME} v{APP_VERSION}")
logger.info(f"Database: {DATABASE_URL}")

# Create a settings object for compatibility with code expecting it
class Settings:
    @property
    def database_url(self):
        return DATABASE_URL
    
    @property
    def debug(self):
        return DEBUG
    
    @property
    def app_name(self):
        return APP_NAME
    
    @property
    def app_version(self):
        return APP_VERSION
    
    @property
    def app_description(self):
        return APP_DESCRIPTION
    
    @property
    def api_prefix(self):
        return API_PREFIX
    
    @property
    def cors_origins(self):
        return CORS_ORIGINS

# Create settings instance for compatibility
settings = Settings()

def get_settings() -> Settings:
    return settings