import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os

# Simple admin token storage (in memory - restart resets tokens)
active_tokens = {}

security = HTTPBasic()

# Read from environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change_this_now')

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

def verify_admin_credentials(username: str, password: str) -> bool:
    """Verify admin credentials (for password change)"""
    from app.admin_auth import ADMIN_USERNAME, ADMIN_PASSWORD
    import secrets
    
    return (secrets.compare_digest(username, ADMIN_USERNAME) and 
            secrets.compare_digest(password, ADMIN_PASSWORD))

def update_admin_password(username: str, new_password: str):
    """Update admin password (you'll need to store this securely)"""
    # This is a placeholder - you should store passwords securely
    # Options:
    # 1. Update environment variable (not persistent)
    # 2. Store in database (recommended)
    # 3. Store in encrypted file
    
    # For now, just print that it would be updated
    print(f"Password would be updated for {username}")
    
    # In production, you'd want to:
    # 1. Hash the password
    # 2. Store in database with user ID
    # 3. Update session
    pass
