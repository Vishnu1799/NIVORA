from fastapi import APIRouter
import httpx
from app.config.settings import settings

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.get("/health")
async def bank_health():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.bank_simulator_url}/health")
            return resp.json()
    except Exception as e:
        return {"status": "UNKNOWN", "error": str(e)}
