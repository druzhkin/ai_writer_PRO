from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["health"])
async def health():
    return {"status": "ok"}

@router.get("", tags=["health"])
async def health_no_slash():
    return {"status": "ok"}