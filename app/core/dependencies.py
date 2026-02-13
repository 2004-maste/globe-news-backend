"""
Dependencies for FastAPI endpoints.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user.
    For now, we'll use a simple implementation.
    """
    # TODO: Implement proper JWT token validation
    if not credentials:
        return None  # Allow anonymous access
    
    try:
        # Placeholder for JWT validation
        # token = credentials.credentials
        # user = authenticate_user(token, db)
        # return user
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session.
    """
    return get_db()


def require_admin(user = Depends(get_current_user)):
    """
    Require admin privileges.
    """
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user


def require_premium(user = Depends(get_current_user)):
    """
    Require premium subscription.
    """
    if not user or user.role not in ["premium", "admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return user