from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...database import get_db
from ...models.article import Article

router = APIRouter()

@router.get("/sources")
async def get_sources(db: Session = Depends(get_db)):
    """Get unique news sources."""
    try:
        sources = db.query(Article.source).distinct().all()
        sources = [s[0] for s in sources if s[0]]
        return {"sources": sources}
    except Exception as e:
        return {"sources": []}