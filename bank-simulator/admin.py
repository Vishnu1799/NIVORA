"""
Admin endpoints for controlling bank simulator state and injecting AUREV AI demo signals.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from state import bank_state
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class ServiceStateRequest(BaseModel):
    state: str  # UP, DOWN, TIMEOUT, DEGRADED, INSUFFICIENT_FUNDS, INVALID_DETAILS, UNKNOWN, ERROR_SIGNAL, NO_RESPONSE
    failure_rate: float = 0.0
    force_outcome: Optional[str] = None
    response_delay_ms: int = 0


class SignalRequest(BaseModel):
    signal: str  # ERROR_SIGNAL, TIMEOUT, NO_RESPONSE, INSTANT_SUCCESS
    transaction_id: Optional[str] = None


@router.post("/service-state")
def set_service_state(req: ServiceStateRequest):
    valid_states = [
        "UP", "DOWN", "TIMEOUT", "DEGRADED", "INSUFFICIENT_FUNDS",
        "INVALID_DETAILS", "UNKNOWN", "ERROR_SIGNAL", "NO_RESPONSE", "INSTANT_SUCCESS"
    ]
    state_normalized = req.state.upper()
    if state_normalized not in valid_states:
        if req.force_outcome and req.force_outcome.upper() in valid_states:
            state_normalized = req.force_outcome.upper()
        else:
            return {"error": f"Invalid state. Must be one of: {valid_states}"}

    bank_state.set_state(
        state=state_normalized,
        failure_rate=req.failure_rate,
        force_outcome=req.force_outcome,
        response_delay_ms=req.response_delay_ms,
    )
    return {
        "success": True,
        "state": state_normalized,
        "failure_rate": req.failure_rate,
        "force_outcome": req.force_outcome,
        "message": f"Bank state set to {state_normalized}",
        "changed_at": datetime.utcnow().isoformat(),
    }


@router.post("/signal")
async def trigger_demo_signal(req: SignalRequest):
    """
    Direct AUREV AI Demo Signal Trigger:
    - ERROR_SIGNAL: Forces connection drop / 500
    - NO_RESPONSE / TIMEOUT: Forces gateway timeout
    - INSTANT_SUCCESS: Delivers late success signal to backend for active UNDER_VERIFICATION payment
    """
    signal = req.signal.upper()

    if signal in ["ERROR_SIGNAL", "TIMEOUT", "NO_RESPONSE"]:
        bank_state.set_state(state=signal, force_outcome=signal)
        return {
            "success": True,
            "signal": signal,
            "message": f"Bank simulator armed with {signal}. Next payment will enter UNDER_VERIFICATION.",
        }

    elif signal == "INSTANT_SUCCESS":
        # 1. Arm bank state as SUCCESS
        bank_state.set_state(state="UP", force_outcome="SUCCESS")
        # 2. Forward signal directly to backend AUREV receiver
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post("http://localhost:8000/api/payments/signal", json={
                    "signal": "INSTANT_SUCCESS",
                    "transaction_id": req.transaction_id
                })
                backend_res = resp.json()
        except Exception as e:
            backend_res = {"error": str(e)}

        return {
            "success": True,
            "signal": "INSTANT_SUCCESS",
            "message": "Instant Success signal delivered to AUREV AI backend.",
            "backend_response": backend_res,
        }

    return {"success": False, "error": f"Unknown signal {signal}"}


@router.get("/service-state")
def get_service_state():
    return {
        "state": bank_state.service_state,
        "failure_rate": bank_state.failure_rate,
        "force_outcome": bank_state.force_outcome,
        "response_delay_ms": bank_state.response_delay_ms,
        "transaction_count": len(bank_state.transactions),
        "state_changed_at": bank_state.state_changed_at.isoformat(),
    }


@router.post("/reset")
def reset_simulator():
    """Reset simulator to clean UP state — clear all transactions."""
    bank_state.transactions.clear()
    bank_state.set_state("UP")
    return {"success": True, "message": "Simulator reset to UP state with no transactions"}


@router.get("/transactions")
def list_transactions():
    """List all processed transactions."""
    return {"count": len(bank_state.transactions), "transactions": list(bank_state.transactions.values())}
