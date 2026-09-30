"""
Admin endpoints for controlling bank simulator state.
Use these to demo different failure scenarios.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from state import bank_state
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])


class ServiceStateRequest(BaseModel):
    state: str  # UP, DOWN, TIMEOUT, DEGRADED, INSUFFICIENT_FUNDS, INVALID_DETAILS, UNKNOWN
    failure_rate: float = 0.0
    force_outcome: Optional[str] = None  # SUCCESS, INSUFFICIENT_FUNDS, INVALID_DETAILS, TIMEOUT, UNKNOWN
    response_delay_ms: int = 0


@router.post("/service-state")
def set_service_state(req: ServiceStateRequest):
    """
    Control bank behavior for demo scenarios.

    Scenarios:
    - {state: 'INSUFFICIENT_FUNDS'} — Persistent insufficient balance
    - {state: 'DOWN'} — Bank completely unavailable
    - {state: 'TIMEOUT'} — Bank gateway times out
    - {state: 'UNKNOWN'} — Reconcilable debit conflict
    - {state: 'DEGRADED', failure_rate: 0.7} — High failure rate
    - {state: 'UP'} — Normal operation
    """
    valid_states = ["UP", "DOWN", "TIMEOUT", "DEGRADED", "INSUFFICIENT_FUNDS", "INVALID_DETAILS", "UNKNOWN"]
    state_normalized = req.state.upper()
    if state_normalized not in valid_states:
        # Check if force_outcome has the state
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


@router.get("/scenarios")
def list_scenarios():
    """List pre-configured demo scenarios."""
    return {
        "scenarios": [
            {"name": "Normal Operation", "description": "All payments succeed",
             "request": {"state": "UP", "failure_rate": 0.0}},
            {"name": "Insufficient Funds", "description": "Persistent insufficient balance on customer account (Decline Code 51)",
             "request": {"state": "INSUFFICIENT_FUNDS"}},
            {"name": "Bank Down", "description": "Bank completely unavailable — payments instantly declined (503)",
             "request": {"state": "DOWN"}},
            {"name": "Network Timeout", "description": "Next payment times out — triggers AUREV AI safe recovery",
             "request": {"state": "TIMEOUT"}},
            {"name": "Unknown Debit Status", "description": "Money debited but unconfirmed — triggers auto-reconciliation",
             "request": {"state": "UNKNOWN"}},
            {"name": "Degraded Latency Mode", "description": "Slow responses + network jitter",
             "request": {"state": "DEGRADED", "failure_rate": 0.5, "response_delay_ms": 3000}},
        ]
    }
