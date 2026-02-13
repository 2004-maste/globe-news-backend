from fastapi import APIRouter

router = APIRouter()

@router.get("/health/status")
async def health_status():
    return {"status": "healthy", "service": "Globe News API"}