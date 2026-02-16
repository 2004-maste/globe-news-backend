import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import hashlib
import hmac

# Simple admin token storage (in memory - restart resets tokens)
# In production, you'd want this in Redis/DB
active_tokens = {}

security = HTTPBasic()

# You can change these - store in env variables
ADMIN_USERNAME = "admin"  # Change this
ADMIN_PASSWORD = "change_this_now"  # Change this immediately

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Basic HTTP auth for admin"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def create_session_token(username: str) -> str:
    """Create a session token after login"""
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=8)
    }
    return token

def verify_session_token(token: str) -> bool:
    """Verify session token"""
    if token not in active_tokens:
        return False
    
    session = active_tokens[token]
    if datetime.utcnow() > session["expires_at"]:
        del active_tokens[token]
        return False
    
    return True

def get_current_admin(request: Request):
    """Get current admin from session token in cookie"""
    token = request.cookies.get("admin_token")
    if not token or not verify_session_token(token):
        return None
    return active_tokens[token].get("username")
