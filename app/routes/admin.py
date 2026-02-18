from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os

from app.database import get_db
from app.models import Article, Category
from app.admin_auth import verify_admin, create_session_token, get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])

# Setup templates
templates = Jinja2Templates(directory="app/templates/admin")

# ==================== ADMIN LOGIN ====================

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "error": None}
    )

@router.post("/login")
async def admin_login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle admin login"""
    # Verify credentials using basic auth logic
    from app.admin_auth import ADMIN_USERNAME, ADMIN_PASSWORD
    import secrets
    
    print(f"DEBUG: Login attempt - username: {username}, password: {password}")
    print(f"DEBUG: Expected - username: {ADMIN_USERNAME}, password: {ADMIN_PASSWORD}")
    
    username_match = secrets.compare_digest(username, ADMIN_USERNAME)
    password_match = secrets.compare_digest(password, ADMIN_PASSWORD)
    
    print(f"DEBUG: username_match: {username_match}, password_match: {password_match}")
    
    if username_match and password_match:
        token = create_session_token(username)
        print(f"DEBUG: Login successful, token created: {token[:10]}...")
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(
            key="admin_token",
            value=token,
            httponly=True,
            max_age=28800,  # 8 hours
            secure=True,
            samesite="lax"
        )
        return response
    
    print("DEBUG: Login failed")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=401
    )

@router.get("/logout")
async def admin_logout(response: Response):
    """Logout admin"""
    response = RedirectResponse(url="/")
    response.delete_cookie("admin_token")
    return response

# ==================== ADMIN DASHBOARD ====================

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    # Get stats
    total_articles = db.query(Article).count()
    pending_articles = db.query(Article).filter(Article.is_approved == False).count()
    approved_articles = db.query(Article).filter(Article.is_approved == True).count()
    categories_count = db.query(Category).count()
    
    # Get recent pending articles
    recent_pending = db.query(Article).filter(
        Article.is_approved == False
    ).order_by(
        Article.published_at.desc()
    ).limit(10).all()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "admin": admin,
            "total_articles": total_articles,
            "pending_articles": pending_articles,
            "approved_articles": approved_articles,
            "categories_count": categories_count,
            "recent_pending": recent_pending
        }
    )

# ==================== ARTICLE REVIEW ====================

@router.get("/articles/pending", response_class=HTMLResponse)
async def pending_articles(
    request: Request,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List pending articles for review"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    skip = (page - 1) * limit
    articles = db.query(Article).filter(
        Article.is_approved == False
    ).order_by(
        Article.published_at.desc()
    ).offset(skip).limit(limit).all()
    
    total = db.query(Article).filter(Article.is_approved == False).count()
    total_pages = (total + limit - 1) // limit
    
    return templates.TemplateResponse(
        "pending_articles.html",
        {
            "request": request,
            "articles": articles,
            "page": page,
            "total_pages": total_pages,
            "total": total
        }
    )

@router.get("/articles/{article_id}/review", response_class=HTMLResponse)
async def review_article(
    request: Request,
    article_id: int,
    db: Session = Depends(get_db)
):
    """Review single article"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return templates.TemplateResponse(
        "review_article.html",
        {
            "request": request,
            "article": article
        }
    )

@router.post("/articles/{article_id}/approve")
async def approve_article(
    request: Request,
    article_id: int,
    db: Session = Depends(get_db)
):
    """Approve article"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.is_approved = True
    article.approved_at = datetime.utcnow()
    article.approved_by = admin
    article.edited_at = datetime.utcnow()
    db.commit()
    
    return RedirectResponse(url="/admin/articles/pending", status_code=303)

@router.post("/articles/{article_id}/reject")
async def reject_article(
    request: Request,
    article_id: int,
    db: Session = Depends(get_db)
):
    """Reject article (will be hidden)"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.is_approved = False
    article.is_rejected = True
    article.rejected_at = datetime.utcnow()
    article.rejected_by = admin
    db.commit()
    
    return RedirectResponse(url="/admin/articles/pending", status_code=303)

@router.post("/articles/{article_id}/edit")
async def edit_article(
    request: Request,
    article_id: int,
    title: str = Form(...),
    description: str = Form(...),
    content: str = Form(...),
    full_content: str = Form(None),
    category_id: int = Form(...),
    is_breaking: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Edit and save article"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.title = title
    article.description = description
    article.content = content
    if full_content:
        article.full_content = full_content
    article.category_id = category_id
    article.is_breaking = is_breaking
    article.is_edited = True
    article.edited_at = datetime.utcnow()
    article.edited_by = admin
    
    db.commit()
    
    return RedirectResponse(url=f"/admin/articles/{article_id}/review", status_code=303)

# ==================== APPROVED ARTICLES MANAGEMENT ====================

@router.get("/articles/approved", response_class=HTMLResponse)
async def approved_articles(
    request: Request,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List approved articles"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    skip = (page - 1) * limit
    articles = db.query(Article).filter(
        Article.is_approved == True
    ).order_by(
        Article.approved_at.desc()
    ).offset(skip).limit(limit).all()
    
    total = db.query(Article).filter(Article.is_approved == True).count()
    total_pages = (total + limit - 1) // limit
    
    return templates.TemplateResponse(
        "approved_articles.html",
        {
            "request": request,
            "articles": articles,
            "page": page,
            "total_pages": total_pages,
            "total": total
        }
    )

# ==================== CATEGORY MANAGEMENT ====================

@router.get("/categories", response_class=HTMLResponse)
async def manage_categories(
    request: Request,
    db: Session = Depends(get_db)
):
    """Manage categories"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    categories = db.query(Category).all()
    return templates.TemplateResponse(
        "categories.html",
        {
            "request": request,
            "categories": categories
        }
    )

@router.post("/categories/add")
async def add_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Add new category"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    category = Category(name=name, description=description)
    db.add(category)
    db.commit()
    
    return RedirectResponse(url="/admin/categories", status_code=303)

# ==================== SETTINGS ====================

@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request):
    """Admin settings"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "admin": admin
        }
    )

@router.post("/articles/bulk-approve")
async def bulk_approve_articles(
    request: Request,
    db: Session = Depends(get_db)
):
    """Approve all pending articles"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    count = db.query(Article).filter(Article.is_approved == False).update(
        {
            'is_approved': True,
            'approved_at': datetime.utcnow(),
            'approved_by': admin,
            'edited_at': datetime.utcnow()
        },
        synchronize_session=False
    )
    db.commit()
    
    return RedirectResponse(url="/admin/articles/approved", status_code=303)

@router.post("/articles/bulk-reject")
async def bulk_reject_articles(
    request: Request,
    db: Session = Depends(get_db)
):
    """Reject all pending articles"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    count = db.query(Article).filter(Article.is_approved == False).update(
        {
            'is_rejected': True,
            'rejected_at': datetime.utcnow(),
            'rejected_by': admin,
            'edited_at': datetime.utcnow()
        },
        synchronize_session=False
    )
    db.commit()
    
    return RedirectResponse(url="/admin/articles/pending", status_code=303)

# ==================== SETTINGS MANAGEMENT ====================

@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    """Admin settings page"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    print(f"DEBUG: admin_settings called by {admin}")
    
    # Simple settings dict for testing
    settings = {
        'site_name': 'Globe News',
        'site_url': 'https://globe-news-jade.vercel.app',
    }
    
    print(f"DEBUG: settings dict: {settings}")
    print(f"DEBUG: settings.site_name: {settings.get('site_name')}")
    
    # Simple system info
    system_info = {
        'python_version': '3.11',
        'db_size': '10 MB',
        'total_articles': 2480,
        'last_fetch': '2024-02-18'
    }
    
    template_data = {
        "request": request,
        "admin": admin,
        "settings": settings,
        "system_info": system_info
    }
    print(f"DEBUG: template_data keys: {template_data.keys()}")
    
    return templates.TemplateResponse("settings.html", template_data)

@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    """Admin settings page"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login")
    
    print("="*50)
    print("ADMIN SETTINGS DEBUG")
    print(f"Admin user: {admin}")
    
    # Settings dict
    settings = {
        'site_name': 'Globe News',
        'site_url': 'https://globe-news-jade.vercel.app',
        'admin_email': 'admin@globenews.com',
        'articles_per_page': 20,
        'cache_ttl': 300,
        'enable_rss_fetch': True,
        'enable_content_extraction': True,
        'enable_preview_generation': True
    }
    
    # System info
    import sys
    import os
    db_path = '/app/data/globe_news.db'
    db_size = "0 MB"
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        db_size = f"{size_bytes / (1024*1024):.1f} MB"
    
    system_info = {
        'python_version': sys.version.split()[0],
        'db_size': db_size,
        'total_articles': db.query(Article).count(),
        'last_fetch': '2024-02-18'
    }
    
    # Create template context
    context = {
        "request": request,
        "admin": admin,
        "settings": settings,
        "system_info": system_info
    }
    
    # Print debug info
    print(f"Context keys: {list(context.keys())}")
    print(f"Settings keys: {list(settings.keys())}")
    print(f"System info keys: {list(system_info.keys())}")
    print("="*50)
    
    return templates.TemplateResponse("settings.html", context)

@router.post("/settings/update")
async def update_settings(
    request: Request,
    response: Response,
    site_name: str = Form(...),
    site_url: str = Form(...),
    admin_email: str = Form(...),
    articles_per_page: int = Form(20),
    cache_ttl: int = Form(300),
    enable_rss_fetch: bool = Form(False),
    enable_content_extraction: bool = Form(False),
    enable_preview_generation: bool = Form(False),
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update settings"""
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login")
    
    # Handle password change if requested
    if current_password and new_password and confirm_password:
        from app.admin_auth import ADMIN_PASSWORD, verify_admin_credentials
        
        # Verify current password
        if not verify_admin_credentials(admin_user, current_password):
            return templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "admin": admin_user,
                    "error": "Current password is incorrect",
                    "settings": {
                        'site_name': site_name,
                        'site_url': site_url,
                        'admin_email': admin_email,
                        'articles_per_page': articles_per_page,
                        'cache_ttl': cache_ttl,
                        'enable_rss_fetch': enable_rss_fetch,
                        'enable_content_extraction': enable_content_extraction,
                        'enable_preview_generation': enable_preview_generation
                    }
                }
            )
        
        if new_password != confirm_password:
            return templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "admin": admin_user,
                    "error": "New passwords do not match",
                    "settings": {
                        'site_name': site_name,
                        'site_url': site_url,
                        'admin_email': admin_email,
                        'articles_per_page': articles_per_page,
                        'cache_ttl': cache_ttl,
                        'enable_rss_fetch': enable_rss_fetch,
                        'enable_content_extraction': enable_content_extraction,
                        'enable_preview_generation': enable_preview_generation
                    }
                }
            )
        
        if len(new_password) < 8:
            return templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "admin": admin_user,
                    "error": "Password must be at least 8 characters",
                    "settings": {
                        'site_name': site_name,
                        'site_url': site_url,
                        'admin_email': admin_email,
                        'articles_per_page': articles_per_page,
                        'cache_ttl': cache_ttl,
                        'enable_rss_fetch': enable_rss_fetch,
                        'enable_content_extraction': enable_content_extraction,
                        'enable_preview_generation': enable_preview_generation
                    }
                }
            )
        
        # Update password (you'll need to implement this in admin_auth.py)
        # update_admin_password(admin_user, new_password)
        
        print(f"Password change requested for {admin_user}")
    
    # Here you would save settings to database or file
    print(f"Settings updated by {admin_user}:")
    print(f"  Site Name: {site_name}")
    print(f"  Site URL: {site_url}")
    print(f"  Articles per page: {articles_per_page}")
    
    # Redirect back to settings with success message
    response = RedirectResponse(url="/admin/settings?success=true", status_code=303)
    return response

@router.post("/admin/articles/{article_id}/save-summary")
async def admin_save_human_summary(
    request: Request,
    article_id: int,
    human_summary: str = Form(None),
    action: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verify admin authentication
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)
    
    # Get the article
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Save the human summary
    article.human_summary = human_summary
    
    # If action is save_and_approve, also approve the article
    if action == "save_and_approve":
        article.is_approved = True
        article.is_rejected = False
        article.approved_at = datetime.utcnow()
        article.approved_by = request.session.get("admin_username", "admin")
    
    # Commit changes
    db.commit()
    
    # Clear cache for this article
    await clear_article_cache(article_id)
    
    # Redirect based on action
    if action == "save_and_approve":
        return RedirectResponse(url="/admin/articles/approved", status_code=303)
    else:
        return RedirectResponse(url=f"/admin/articles/{article_id}/review", status_code=303)
