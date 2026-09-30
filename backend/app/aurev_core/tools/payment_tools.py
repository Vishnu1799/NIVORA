"""
Consolidated Payment Tools for AUREV.
Maintains backward compatibility with test payments while exposing all observation,
action, and monitoring tools.
"""
import os
import sys

# Ensure parent root is in sys.path when invoked directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Any, Dict, Optional
from memory.payment_memory import payment_memory
from tools.observation_tools import (
    get_payment_state as obs_get_payment_state,
    get_attempt_history,
    get_gateway_status,
    get_server_health,
    get_webhook_status,
    get_transaction_status,
    get_customer_session,
    get_risk_signals,
    get_reconciliation_status,
    set_system_health,
)
from tools.action_tools import (
    block_pay_again,
    allow_retry,
    create_recovery_permit,
    request_payment_status,
    trigger_reconciliation,
    switch_gateway,
    create_support_case,
    trigger_eligible_refund,
    notify_user,
    notify_merchant,
)
from tools.monitoring_tools import (
    watch_payment,
    watch_gateway,
    watch_server,
    watch_webhook,
    watch_reconciliation,
)


def get_payment_state(payment_id: str) -> Dict[str, Any]:
    """
    Backward-compatible payment status getter.
    Returns payment_id and status (SUCCESS, FAILED, UNKNOWN, PROCESSING, NOT_FOUND).
    """
    attempt = payment_memory.get_attempt(payment_id)
    if attempt is None:
        return {
            "payment_id": payment_id,
            "status": "NOT_FOUND"
        }
    return {
        "payment_id": payment_id,
        "status": attempt.gateway_status
    }


if __name__ == "__main__":
    print(get_payment_state("PAY001"))
    print(get_payment_state("PAY002"))
    print(get_payment_state("PAY003"))
    print(get_payment_state("PAY004"))
    print(get_payment_state("PAY999"))