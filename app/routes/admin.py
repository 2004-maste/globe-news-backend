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
