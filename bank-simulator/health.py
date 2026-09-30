from fastapi import APIRouter
from state import bank_state
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/health")
def get_health():
    """
    Check bank service health.
    Returns: UP, DOWN, TIMEOUT, DEGRADED
    """
    latency = bank_state.get_latency_ms() if bank_state.service_state != "DOWN" else 0
    return {
        "status": bank_state.service_state,
        "latency_ms": latency,
        "service": "NIVORA Bank Simulator",
        "timestamp": datetime.utcnow().isoformat(),
        "failure_rate": bank_state.failure_rate,
    }
