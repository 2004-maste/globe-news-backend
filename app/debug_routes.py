"""
Debug script to check registered routes
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

print("=== Registered Routes ===")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"Path: {route.path}")
        print(f"  Name: {route.name}")
        print(f"  Methods: {route.methods if hasattr(route, 'methods') else 'N/A'}")
        print()
print("========================")