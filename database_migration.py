#!/usr/bin/env python3
"""
Database Migration Script for Globe News v8.0.0
"""

import sqlite3
import os

def migrate_database():
    """Migrate database to v8.0.0 schema"""
    DATABASE = "globe_news.db"
    
    if not os.path.exists(DATABASE):
        print("Database not found. Creating new database...")
        return
    
    print(f"Migrating database {DATABASE} to v8.0.0 schema...")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check current structure of categories table
    cursor.execute("PRAGMA table_info(categories)")
    category_columns = [col[1] for col in cursor.fetchall()]
    print(f"Current categories columns: {category_columns}")
    
    # Check current structure of articles table
    cursor.execute("PRAGMA table_info(articles)")
    article_columns = [col[1] for col in cursor.fetchall()]
    print(f"Current articles columns: {article_columns}")
    
    # ===== MIGRATE CATEGORIES TABLE =====
    if 'display_name' not in category_columns:
        print("\nMigrating categories table...")
        
        # Backup old categories
        cursor.execute("SELECT * FROM categories")
        old_categories = cursor.fetchall()
        print(f"Found {len(old_categories)} existing categories")
        
        # Drop and recreate categories table with new schema
        cursor.execute("DROP TABLE IF EXISTS categories_old")
        cursor.execute("ALTER TABLE categories RENAME TO categories_old")
        
        # Create new categories table
        cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            color TEXT NOT NULL,
            icon TEXT NOT NULL
        )
        ''')
        
        # Default categories for v8.0.0
        default_categories = [
            ('world', 'World', '#4A90E2', 'globe'),
            ('technology', 'Technology', '#7B1FA2', 'cpu'),
            ('business', 'Business', '#388E3C', 'trending-up'),
            ('science', 'Science', '#D32F2F', 'flask'),
            ('entertainment', 'Entertainment', '#F57C00', 'film'),
            ('sports', 'Sports', '#1976D2', 'trophy'),
            ('health', 'Health', '#C2185B', 'heart'),
            ('politics', 'Politics', '#455A64', 'flag'),
            ('general', 'General', '#607D8B', 'grid')
        ]
        
        # Insert default categories
        for cat_name, display_name, color, icon in default_categories:
            cursor.execute('''
            INSERT OR IGNORE INTO categories (name, display_name, color, icon) 
            VALUES (?, ?, ?, ?)
            ''', (cat_name, display_name, color, icon))
        
        print("✅ Categories table migrated successfully")
    
    # ===== MIGRATE ARTICLES TABLE =====
    print("\nMigrating articles table...")
    
    # Add missing columns to articles table
    missing_columns = []
    
    if 'category' not in article_columns:
        missing_columns.append('category')
        cursor.execute("ALTER TABLE articles ADD COLUMN category TEXT DEFAULT 'general'")
    
    if 'language' not in article_columns:
        missing_columns.append('language')
        cursor.execute("ALTER TABLE articles ADD COLUMN language TEXT DEFAULT 'english'")
    
    if 'preview_generated' not in article_columns:
        missing_columns.append('preview_generated')
        cursor.execute("ALTER TABLE articles ADD COLUMN preview_generated BOOLEAN DEFAULT 0")
    
    if 'is_breaking' not in article_columns:
        missing_columns.append('is_breaking')
        cursor.execute("ALTER TABLE articles ADD COLUMN is_breaking BOOLEAN DEFAULT 0")
    
    if 'content_preview' not in article_columns:
        missing_columns.append('content_preview')
        cursor.execute("ALTER TABLE articles ADD COLUMN content_preview TEXT")
    
    if missing_columns:
        print(f"✅ Added missing columns: {missing_columns}")
    else:
        print("✅ Articles table is already up to date")
    
    # Update any existing articles with default values
    cursor.execute("UPDATE articles SET category = 'general' WHERE category IS NULL")
    cursor.execute("UPDATE articles SET language = 'english' WHERE language IS NULL")
    cursor.execute("UPDATE articles SET preview_generated = 0 WHERE preview_generated IS NULL")
    cursor.execute("UPDATE articles SET is_breaking = 0 WHERE is_breaking IS NULL")
    
    # ===== CREATE INDEXES =====
    print("\nCreating indexes...")
    
    # Drop existing indexes if they exist
    try:
        cursor.execute("DROP INDEX IF EXISTS idx_language")
        cursor.execute("DROP INDEX IF EXISTS idx_published")
        cursor.execute("DROP INDEX IF EXISTS idx_category")
        cursor.execute("DROP INDEX IF EXISTS idx_breaking")
    except:
        pass
    
    # Create new indexes
    try:
        cursor.execute('CREATE INDEX idx_language ON articles(language)')
        print("✅ Created idx_language")
    except Exception as e:
        print(f"⚠️  Could not create idx_language: {e}")
    
    try:
        cursor.execute('CREATE INDEX idx_published ON articles(published_at)')
        print("✅ Created idx_published")
    except Exception as e:
        print(f"⚠️  Could not create idx_published: {e}")
    
    try:
        cursor.execute('CREATE INDEX idx_category ON articles(category)')
        print("✅ Created idx_category")
    except Exception as e:
        print(f"⚠️  Could not create idx_category: {e}")
    
    try:
        cursor.execute('CREATE INDEX idx_breaking ON articles(is_breaking)')
        print("✅ Created idx_breaking")
    except Exception as e:
        print(f"⚠️  Could not create idx_breaking: {e}")
    
    # ===== VERIFY MIGRATION =====
    print("\nVerifying migration...")
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    category_count = cursor.fetchone()[0]
    print(f"Categories in database: {category_count}")
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    article_count = cursor.fetchone()[0]
    print(f"Articles in database: {article_count}")
    
    cursor.execute("PRAGMA table_info(categories)")
    final_category_columns = [col[1] for col in cursor.fetchall()]
    print(f"Final categories columns: {final_category_columns}")
    
    cursor.execute("PRAGMA table_info(articles)")
    final_article_columns = [col[1] for col in cursor.fetchall()]
    print(f"Final articles columns: {final_article_columns}")
    
    # Clean up
    cursor.execute("DROP TABLE IF EXISTS categories_old")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("✅ DATABASE MIGRATION COMPLETE!")
    print("="*50)
    print(f"Database: {DATABASE}")
    print(f"Categories: {category_count}")
    print(f"Articles: {article_count}")
    print(f"Schema: v8.0.0")
    print("="*50)

if __name__ == "__main__":
    migrate_database()