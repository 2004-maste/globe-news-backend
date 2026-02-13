from datetime import datetime, timedelta
import json
import secrets
from typing import Optional, Dict, Any
import sqlite3
import hashlib
import jwt
from auth_config import AuthConfig

class User:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        self.cursor = db_conn.cursor()
    
    def create_user(self, email: str, username: str = None, display_name: str = None,
                   avatar_url: str = None, auth_provider: str = 'local',
                   provider_id: str = None, password: str = None) -> Optional[int]:
        """Create a new user."""
        try:
            # Hash password if provided
            password_hash = None
            if password and auth_provider == 'local':
                salt = secrets.token_hex(16)
                hashed = hashlib.sha256((password + salt).encode()).hexdigest()
                password_hash = f"{salt}${hashed}"
            
            self.cursor.execute('''
            INSERT INTO users (email, username, display_name, avatar_url, 
                              auth_provider, provider_id, password_hash, 
                              created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                username or email.split('@')[0],
                display_name or email.split('@')[0],
                avatar_url,
                auth_provider,
                provider_id,
                password_hash,
                datetime.now(),
                datetime.now()
            ))
            
            user_id = self.cursor.lastrowid
            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            # User already exists
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email: str, auth_provider: str = 'local') -> Optional[Dict]:
        """Get user by email and auth provider."""
        try:
            self.cursor.execute(
                'SELECT * FROM users WHERE email = ? AND auth_provider = ?',
                (email, auth_provider)
            )
            user = self.cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        try:
            self.cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = self.cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def verify_password(self, email: str, password: str) -> Optional[Dict]:
        """Verify local user password."""
        user = self.get_user_by_email(email, 'local')
        if not user or not user.get('password_hash'):
            return None
        
        salt, stored_hash = user['password_hash'].split('$')
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        if test_hash == stored_hash:
            # Update last login
            self.cursor.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.now(), user['id'])
            )
            self.conn.commit()
            return user
        return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Update user preferences."""
        try:
            current_prefs = self.get_user_preferences(user_id)
            current_prefs.update(preferences)
            
            self.cursor.execute(
                'UPDATE users SET preferences = ? WHERE id = ?',
                (json.dumps(current_prefs), user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences."""
        try:
            self.cursor.execute(
                'SELECT preferences FROM users WHERE id = ?',
                (user_id,)
            )
            result = self.cursor.fetchone()
            if result and result['preferences']:
                return json.loads(result['preferences'])
            return {}
        except Exception as e:
            print(f"Error getting preferences: {e}")
            return {}
    
    def create_or_update_oauth_user(self, email: str, name: str, picture: str,
                                   provider: str, provider_id: str) -> Dict:
        """Create or update user from OAuth provider."""
        # Try to get existing user
        user = self.get_user_by_email(email, provider)
        
        if user:
            # Update existing user
            self.cursor.execute('''
            UPDATE users SET 
                display_name = ?,
                avatar_url = ?,
                last_login = ?
            WHERE id = ?
            ''', (name, picture, datetime.now(), user['id']))
        else:
            # Create new user
            user_id = self.create_user(
                email=email,
                display_name=name,
                avatar_url=picture,
                auth_provider=provider,
                provider_id=provider_id
            )
            if user_id:
                user = self.get_user_by_id(user_id)
        
        self.conn.commit()
        return user if user else None

class SessionManager:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        self.cursor = db_conn.cursor()
    
    def create_session(self, user_id: int, data: Dict = None) -> str:
        """Create a new session for user."""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=AuthConfig.SESSION_LIFETIME)
        
        self.cursor.execute('''
        INSERT INTO sessions (session_id, user_id, data, expires_at)
        VALUES (?, ?, ?, ?)
        ''', (
            session_id,
            user_id,
            json.dumps(data or {}),
            expires_at
        ))
        self.conn.commit()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID if not expired."""
        try:
            self.cursor.execute('''
            SELECT s.*, u.email, u.username, u.display_name, u.is_admin
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_id = ? AND s.expires_at > ?
            ''', (session_id, datetime.now()))
            
            session = self.cursor.fetchone()
            if session:
                return dict(session)
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            self.cursor.execute(
                'DELETE FROM sessions WHERE session_id = ?',
                (session_id,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            self.cursor.execute(
                'DELETE FROM sessions WHERE expires_at <= ?',
                (datetime.now(),)
            )
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            return deleted_count
        except Exception as e:
            print(f"Error cleaning sessions: {e}")
            return 0

class BookmarkManager:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        self.cursor = db_conn.cursor()
    
    def add_bookmark(self, user_id: int, article_id: int) -> bool:
        """Add article to user's bookmarks."""
        try:
            self.cursor.execute('''
            INSERT OR IGNORE INTO bookmarks (user_id, article_id)
            VALUES (?, ?)
            ''', (user_id, article_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding bookmark: {e}")
            return False
    
    def remove_bookmark(self, user_id: int, article_id: int) -> bool:
        """Remove article from user's bookmarks."""
        try:
            self.cursor.execute('''
            DELETE FROM bookmarks WHERE user_id = ? AND article_id = ?
            ''', (user_id, article_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error removing bookmark: {e}")
            return False
    
    def get_user_bookmarks(self, user_id: int, limit: int = 50, offset: int = 0) -> list:
        """Get user's bookmarked articles."""
        try:
            self.cursor.execute('''
            SELECT a.*, b.created_at as bookmarked_at
            FROM articles a
            JOIN bookmarks b ON a.id = b.article_id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
            LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error getting bookmarks: {e}")
            return []
    
    def is_bookmarked(self, user_id: int, article_id: int) -> bool:
        """Check if article is bookmarked by user."""
        try:
            self.cursor.execute('''
            SELECT 1 FROM bookmarks 
            WHERE user_id = ? AND article_id = ?
            ''', (user_id, article_id))
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking bookmark: {e}")
            return False