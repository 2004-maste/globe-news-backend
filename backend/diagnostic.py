#!/usr/bin/env python3
"""
Diagnostic Script for Globe News
"""

import sqlite3
import requests
import json
from datetime import datetime

def check_database():
    """Check database contents"""
    print("="*60)
    print("DATABASE DIAGNOSTIC")
    print("="*60)
    
    db_path = "globe_news.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📊 Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check articles table structure
        print("\n📋 Articles table structure:")
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Count articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        print(f"\n📰 Total articles: {article_count}")
        
        # Show recent articles
        print(f"\n📅 Recent articles (last 10):")
        cursor.execute("""
            SELECT id, title, category, source, published_at 
            FROM articles 
            ORDER BY published_at DESC 
            LIMIT 10
        """)
        articles = cursor.fetchall()
        
        if articles:
            for art in articles:
                print(f"  [{art[0]}] {art[1][:50]}...")
                print(f"     Category: {art[2]}, Source: {art[3]}, Date: {art[4][:10]}")
        else:
            print("  No articles found!")
        
        # Check categories
        print(f"\n🏷️  Categories:")
        cursor.execute("SELECT name, display_name FROM categories")
        categories = cursor.fetchall()
        for cat in categories:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE category = ?", (cat[0],))
            count = cursor.fetchone()[0]
            print(f"  {cat[1]}: {count} articles")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_backend_api():
    """Check backend API endpoints"""
    print("\n" + "="*60)
    print("BACKEND API DIAGNOSTIC")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    try:
        # Check health endpoint
        print("🔧 Health check:")
        try:
            response = requests.get(f"{base_url}/api/v1/health/status", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"  ✅ Status: {health_data.get('status', 'unknown')}")
                print(f"  📊 Articles in DB: {health_data.get('database', {}).get('articles', 0)}")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
        
        # Check articles endpoint
        print("\n📰 Articles endpoint:")
        try:
            response = requests.get(f"{base_url}/api/v1/articles?limit=5", timeout=5)
            if response.status_code == 200:
                articles = response.json()
                print(f"  ✅ Got {len(articles)} articles")
                if articles:
                    for i, art in enumerate(articles[:3]):
                        print(f"    {i+1}. {art.get('title', 'No title')[:60]}...")
                        print(f"       ID: {art.get('id')}, Category: {art.get('category')}")
                else:
                    print("  ⚠️  No articles returned from API")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Articles endpoint failed: {e}")
        
        # Check categories endpoint
        print("\n🏷️  Categories endpoint:")
        try:
            response = requests.get(f"{base_url}/api/v1/categories", timeout=5)
            if response.status_code == 200:
                categories = response.json()
                print(f"  ✅ Got {len(categories)} categories")
                for cat in categories[:5]:
                    print(f"    - {cat.get('display_name')} ({cat.get('name')})")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Categories endpoint failed: {e}")
            
    except Exception as e:
        print(f"❌ API diagnostic failed: {e}")

def check_frontend():
    """Check frontend"""
    print("\n" + "="*60)
    print("FRONTEND DIAGNOSTIC")
    print("="*60)
    
    frontend_url = "http://localhost:5000"
    
    try:
        print("🌐 Checking frontend homepage:")
        try:
            response = requests.get(frontend_url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Frontend is running (HTTP 200)")
                # Check if page contains article indicators
                html = response.text.lower()
                if 'article' in html or 'news' in html or 'card' in html:
                    print(f"  ✅ Page contains article/content elements")
                else:
                    print(f"  ⚠️  Page doesn't seem to have article elements")
            else:
                print(f"  ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ Frontend not reachable: {e}")
            
    except Exception as e:
        print(f"❌ Frontend diagnostic failed: {e}")

def fix_database():
    """Fix common database issues"""
    print("\n" + "="*60)
    print("DATABASE FIX ATTEMPT")
    print("="*60)
    
    db_path = "globe_news.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop and recreate articles table with proper schema
        print("🔄 Recreating articles table...")
        
        # First, backup existing data
        cursor.execute("SELECT * FROM articles")
        existing_data = cursor.fetchall()
        existing_count = len(existing_data)
        print(f"  Found {existing_count} existing articles to backup")
        
        # Drop table
        cursor.execute("DROP TABLE IF EXISTS articles_old")
        cursor.execute("ALTER TABLE articles RENAME TO articles_old")
        
        # Create new table with correct schema
        cursor.execute('''
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            language TEXT DEFAULT 'english',
            published_at TIMESTAMP NOT NULL,
            content_preview TEXT,
            preview_generated BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_breaking BOOLEAN DEFAULT 0
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX idx_articles_category ON articles(category)')
        cursor.execute('CREATE INDEX idx_articles_published ON articles(published_at DESC)')
        
        conn.commit()
        print("  ✅ Created new articles table")
        
        # If we had existing data, try to restore it
        if existing_data:
            print(f"  🔄 Restoring {existing_count} articles...")
            restored = 0
            for article in existing_data:
                try:
                    # Assuming the old table had similar structure
                    # Adjust indices based on your old schema
                    cursor.execute('''
                    INSERT INTO articles (title, description, url, source, category, 
                                         language, published_at, content_preview, 
                                         preview_generated, created_at, is_breaking)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', article[:11])  # Take first 11 columns
                    restored += 1
                except Exception as e:
                    print(f"    ❌ Failed to restore article: {e}")
                    continue
            
            print(f"  ✅ Restored {restored}/{existing_count} articles")
        
        # Ensure categories table exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            color TEXT NOT NULL,
            icon TEXT NOT NULL
        )
        ''')
        
        # Insert default categories
        categories = [
            ('world', 'World News', '#4A90E2', 'globe'),
            ('technology', 'Technology', '#7B1FA2', 'cpu'),
            ('business', 'Business', '#388E3C', 'trending-up'),
            ('science', 'Science', '#D32F2F', 'flask'),
            ('entertainment', 'Entertainment', '#F57C00', 'film'),
            ('sports', 'Sports', '#1976D2', 'trophy'),
            ('health', 'Health', '#C2185B', 'heart'),
            ('politics', 'Politics', '#455A64', 'flag'),
            ('general', 'General News', '#607D8B', 'newspaper')
        ]
        
        for cat_name, display_name, color, icon in categories:
            cursor.execute('''
            INSERT OR IGNORE INTO categories (name, display_name, color, icon)
            VALUES (?, ?, ?, ?)
            ''', (cat_name, display_name, color, icon))
        
        conn.commit()
        print("✅ Database fix completed")
        
        # Verify the fix
        cursor.execute("SELECT COUNT(*) FROM articles")
        final_count = cursor.fetchone()[0]
        print(f"📊 Final article count: {final_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")

def create_test_article():
    """Create a test article to verify system works"""
    print("\n" + "="*60)
    print("CREATING TEST ARTICLE")
    print("="*60)
    
    db_path = "globe_news.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a test article
        test_article = {
            'title': 'Test Article - Globe News System Check',
            'description': 'This is a test article to verify the Globe News system is working correctly.',
            'url': 'https://example.com/test-article',
            'source': 'Globe News Test',
            'category': 'general',
            'language': 'english',
            'published_at': datetime.now().isoformat(),
            'is_breaking': False
        }
        
        cursor.execute('''
        INSERT OR REPLACE INTO articles 
        (title, description, url, source, category, language, published_at, is_breaking)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_article['title'],
            test_article['description'],
            test_article['url'],
            test_article['source'],
            test_article['category'],
            test_article['language'],
            test_article['published_at'],
            test_article['is_breaking']
        ))
        
        conn.commit()
        print("✅ Created test article")
        print(f"   Title: {test_article['title']}")
        print(f"   URL: {test_article['url']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to create test article: {e}")

def main():
    """Main diagnostic function"""
    print("🌐 GLOBE NEWS DIAGNOSTIC TOOL")
    print("="*60)
    
    # Run diagnostics
    check_database()
    check_backend_api()
    check_frontend()
    
    # Ask if user wants to fix database
    print("\n" + "="*60)
    response = input("Do you want to fix the database? (y/n): ")
    if response.lower() == 'y':
        fix_database()
        create_test_article()
        
        # Re-run diagnostics
        print("\n" + "="*60)
        print("RE-RUNNING DIAGNOSTICS AFTER FIX")
        print("="*60)
        check_database()
        check_backend_api()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nNEXT STEPS:")
    print("1. Check if backend is running: python main.py")
    print("2. Check if frontend is running: python app.py")
    print("3. Visit http://localhost:5000")
    print("4. Check API: http://localhost:8000/api/v1/articles")
    print("="*60)

if __name__ == "__main__":
    main()