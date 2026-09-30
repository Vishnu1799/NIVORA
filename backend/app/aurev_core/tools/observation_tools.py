"""
Observation Tools for AUREV.
Read-only inspection of payment sessions, attempts, telemetry, and system health.
"""
from typing import Any, Dict, List, Optional
from memory.payment_memory import payment_memory
from memory.event_timeline import timeline_store
from models.decisions import SystemHealthState
from models.enums import GatewayStatus, ServerStatus
from models.risk import MLRiskRequest
from ml.factory import get_ml_provider


def get_payment_state(payment_id: str) -> Dict[str, Any]:
    """Inspects the recorded status and state of a payment ID."""
    attempt = payment_memory.get_attempt(payment_id)
    if not attempt:
        return {
            "payment_id": payment_id,
            "status": "NOT_FOUND",
            "found": False
        }
    session = payment_memory.get_session_by_payment_id(payment_id)
    return {
        "payment_id": payment_id,
        "order_id": session.order_id if session else None,
        "status": attempt.gateway_status,
        "bank_status": attempt.bank_status.value,
        "merchant_status": attempt.merchant_status.value,
        "customer_debited": attempt.customer_debited,
        "merchant_credited": attempt.merchant_credited,
        "finality_state": session.finality_state.value if session else "UNKNOWN",
        "decision": session.current_decision.value if session else "WAIT",
        "is_pay_again_blocked": session.is_pay_again_blocked if session else False,
        "found": True
    }


def get_attempt_history(order_id: Optional[str] = None, payment_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all payment attempts associated with an order or payment."""
    session = None
    if order_id:
        session = payment_memory.get_session_by_order_id(order_id)
    elif payment_id:
        session = payment_memory.get_session_by_payment_id(payment_id)

    if not session:
        return []

    return [
        {
            "attempt_number": a.attempt_number,
            "payment_id": a.payment_id,
            "transaction_id": a.transaction_id,
            "amount": a.amount,
            "gateway": a.gateway,
            "gateway_status": a.gateway_status,
            "bank_status": a.bank_status.value,
            "merchant_status": a.merchant_status.value,
            "customer_debited": a.customer_debited,
            "merchant_credited": a.merchant_credited,
            "created_at": a.created_at.isoformat()
        }
        for a in session.attempts
    ]


# Simulated system health state that can be toggled in tests
_system_health = SystemHealthState(
    gateway_status=GatewayStatus.HEALTHY,
    server_status=ServerStatus.HEALTHY,
    error_rate=0.02,
    avg_latency_ms=45.0,
    is_safety_mode_active=False
)


def get_server_health() -> Dict[str, Any]:
    """Retrieves real-time telemetry on server latency, error rate, and financial safety mode."""
    return _system_health.model_dump()


def set_system_health(
    gateway_status: Optional[GatewayStatus] = None,
    server_status: Optional[ServerStatus] = None,
    error_rate: Optional[float] = None,
    avg_latency_ms: Optional[float] = None,
    is_safety_mode_active: Optional[bool] = None,
    active_issues: Optional[List[str]] = None
) -> SystemHealthState:
    """Updates health metrics (useful for outage simulations)."""
    global _system_health
    if gateway_status is not None:
        _system_health.gateway_status = gateway_status
    if server_status is not None:
        _system_health.server_status = server_status
    if error_rate is not None:
        _system_health.error_rate = error_rate
    if avg_latency_ms is not None:
        _system_health.avg_latency_ms = avg_latency_ms
    if is_safety_mode_active is not None:
        _system_health.is_safety_mode_active = is_safety_mode_active
    if active_issues is not None:
        _system_health.active_issues = active_issues
    return _system_health


def get_gateway_status(gateway_name: str = "RAZORPAY") -> Dict[str, Any]:
    """Checks the operational status and latency of a payment gateway."""
    return {
        "gateway": gateway_name,
        "status": _system_health.gateway_status.value,
        "error_rate": _system_health.error_rate,
        "avg_latency_ms": _system_health.avg_latency_ms
    }


def get_webhook_status(payment_id: str) -> Dict[str, Any]:
    """Inspects webhook event delivery history for a payment."""
    events = timeline_store.get_events_for_payment(payment_id)
    webhook_events = [e for e in events if "WEBHOOK" in e.event_type.value]
    attempt = payment_memory.get_attempt(payment_id)

    return {
        "payment_id": payment_id,
        "webhook_received": attempt.webhook_received if attempt else False,
        "event_count": len(webhook_events),
        "events": [
            {
                "type": e.event_type.value,
                "timestamp": e.timestamp.isoformat(),
                "status": e.status,
                "metadata": e.metadata
            }
            for e in webhook_events
        ]
    }


def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
    """Looks up transaction records across all sessions."""
    for session in payment_memory._sessions.values():
        for att in session.attempts:
            if att.transaction_id == transaction_id:
                return {
                    "transaction_id": transaction_id,
                    "payment_id": att.payment_id,
                    "order_id": session.order_id,
                    "status": att.gateway_status,
                    "customer_debited": att.customer_debited
                }
    return {"transaction_id": transaction_id, "found": False}


def get_customer_session(order_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves session metadata for an order."""
    session = payment_memory.get_session_by_order_id(order_id)
    if not session:
        return None
    return session.model_dump()


def get_risk_signals(payment_id: str) -> Dict[str, Any]:
    """Fetches ML risk signals for a payment ID."""
    session = payment_memory.get_session_by_payment_id(payment_id)
    if not session:
        return {"error": "Payment session not found"}
    attempt = session.get_attempt(payment_id) or session.get_latest_attempt()
    if not attempt:
        return {"error": "Payment attempt not found"}

    provider = get_ml_provider()
    req = MLRiskRequest(
        payment_id=payment_id,
        order_id=session.order_id,
        amount=attempt.amount,
        gateway=attempt.gateway,
        attempt_number=attempt.attempt_number,
        gateway_status=attempt.gateway_status,
        customer_debited=attempt.customer_debited,
        bank_status=attempt.bank_status.value,
        merchant_status=attempt.merchant_status.value,
        previous_attempts=len(session.attempts) - 1,
        same_order_previous_success=session.has_successful_attempt()
    )
    res = provider.analyze_payment(req)
    return res.model_dump()


def get_reconciliation_status(order_id: str) -> Dict[str, Any]:
    """Retrieves reconciliation status and records for an order."""
    session = payment_memory.get_session_by_order_id(order_id)
    if not session:
        return {"order_id": order_id, "status": "NOT_FOUND"}
    return {
        "order_id": order_id,
        "reconciliation_state": session.reconciliation_state.value,
        "finality_state": session.finality_state.value,
        "attempts": len(session.attempts)
    }
