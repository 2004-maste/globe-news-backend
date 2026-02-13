#!/usr/bin/env python3
"""
CLEANUP SCRIPT: Remove all fallback articles from database
"""
import sqlite3
import sys

def clean_fallbacks():
    """Remove all fallback/sample articles from the database."""
    try:
        conn = sqlite3.connect('globe_news.db')
        cursor = conn.cursor()
        
        print("="*60)
        print("🗑️  CLEANING FALLBACK ARTICLES FROM DATABASE")
        print("="*60)
        
        # 1. Count before cleanup
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_before = cursor.fetchone()[0]
        
        # 2. Count fallbacks (example.com URLs and fake sources)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE url LIKE '%example.com%' 
               OR source IN ('Tech News', 'Financial Times', 'Global News', 
                           'Medical Journal', 'Sports Network', 'Tech Review')
        """)
        fallback_count = cursor.fetchone()[0]
        
        # 3. Count real articles
        real_count = total_before - fallback_count
        
        print(f"📊 DATABASE STATUS BEFORE CLEANUP:")
        print(f"   Total articles: {total_before}")
        print(f"   Real articles: {real_count}")
        print(f"   Fallback articles: {fallback_count}")
        print("="*60)
        
        if fallback_count == 0:
            print("✅ No fallback articles found!")
            print("\n🎯 Your database already contains only real news articles.")
            conn.close()
            return
        
        # 4. DELETE fallback articles
        print(f"\n🗑️  DELETING {fallback_count} fallback articles...")
        cursor.execute("""
            DELETE FROM articles 
            WHERE url LIKE '%example.com%' 
               OR source IN ('Tech News', 'Financial Times', 'Global News',
                           'Medical Journal', 'Sports Network', 'Tech Review')
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        # 5. Count after cleanup
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_after = cursor.fetchone()[0]
        
        print(f"✅ Successfully deleted {deleted_count} fallback articles")
        print(f"📊 DATABASE STATUS AFTER CLEANUP:")
        print(f"   Total articles: {total_after}")
        print(f"   Removed: {deleted_count}")
        print("="*60)
        
        # 6. Show remaining real articles
        print("\n📰 REAL ARTICLES REMAINING (Sample):")
        cursor.execute("""
            SELECT id, title, source, published_at 
            FROM articles 
            ORDER BY published_at DESC 
            LIMIT 5
        """)
        
        articles = cursor.fetchall()
        if articles:
            for i, (art_id, title, source, date) in enumerate(articles, 1):
                print(f"   {i}. #{art_id}: {title[:60]}...")
                print(f"      Source: {source} | Date: {date[:16]}")
        else:
            print("   No articles found in database")
        
        # 7. Show sources breakdown
        print("\n📊 SOURCES BREAKDOWN:")
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM articles 
            GROUP BY source 
            ORDER BY count DESC
        """)
        
        sources = cursor.fetchall()
        for source, count in sources:
            print(f"   {source}: {count} articles")
        
        conn.close()
        
        print("\n" + "="*60)
        print("🎯 NEXT STEPS:")
        print("   1. Restart your backend: python main.py")
        print("   2. Visit: http://localhost:5000/")
        print("   3. Trigger a fresh fetch if needed:")
        print("      curl -X POST http://localhost:8000/api/v1/fetcher/fetch-now")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clean_fallbacks()