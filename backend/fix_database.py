#!/usr/bin/env python3
"""
Fix database by adding missing preview_content column
"""
import sqlite3
import sys

def fix_database():
    """Add preview_content column to articles table if missing."""
    try:
        print("🔧 Fixing database schema...")
        
        # Connect to database
        conn = sqlite3.connect('globe_news.db')
        cursor = conn.cursor()
        
        # Check if preview_content column exists
        cursor.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'preview_content' not in columns:
            print("➕ Adding preview_content column...")
            cursor.execute('''
                ALTER TABLE articles 
                ADD COLUMN preview_content TEXT
            ''')
            conn.commit()
            print("✅ Column added successfully!")
        else:
            print("✅ Column already exists!")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        print(f"📊 Database has {count} articles")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\n🎉 Database fixed! Restart your backend server.")
    else:
        print("\n💥 Failed to fix database.")
        sys.exit(1)