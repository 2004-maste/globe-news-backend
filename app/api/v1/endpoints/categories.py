from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...database import get_db
from ...models.article import Category

router = APIRouter()

@router.get("")
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories