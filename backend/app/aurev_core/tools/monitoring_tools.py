"""
Monitoring Tools for AUREV.
Provides monitoring probes and listener hooks.
"""
from typing import Any, Dict
from tools.observation_tools import (
    get_payment_state,
    get_gateway_status,
    get_server_health,
    get_webhook_status,
    get_reconciliation_status,
)


def watch_payment(payment_id: str) -> Dict[str, Any]:
    """Probes current state and monitoring status for a payment session."""
    state = get_payment_state(payment_id)
    return {
        "payment_id": payment_id,
        "current_status": state.get("status"),
        "finality_state": state.get("finality_state"),
        "decision": state.get("decision"),
        "monitoring_active": not state.get("finality_state") in ["FINAL_SUCCESS", "FINAL_FAILURE"]
    }


def watch_gateway(gateway_name: str = "RAZORPAY") -> Dict[str, Any]:
    """Probes gateway latency and health."""
    return get_gateway_status(gateway_name)


def watch_server() -> Dict[str, Any]:
    """Probes server latency, error rate, and safety mode status."""
    return get_server_health()


def watch_webhook(payment_id: str) -> Dict[str, Any]:
    """Probes webhook delivery state."""
    return get_webhook_status(payment_id)


def watch_reconciliation(order_id: str) -> Dict[str, Any]:
    """Probes reconciliation progress."""
    return get_reconciliation_status(order_id)
