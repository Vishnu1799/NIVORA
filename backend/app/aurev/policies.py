"""
Safety Policy Engine — Deterministic gate for all AUREV AI actions.
No LLM output can bypass this engine.
"""
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

MAX_RECOVERY_ATTEMPTS = 2

PERMITTED_ACTIONS = {
    # (failure_category, money_debited, bank_health, attempt_count) -> allowed actions
}


def get_permitted_actions(
    failure_category: str,
    money_debited: Optional[bool],
    bank_health: str,
    recovery_attempt_count: int,
    error_code: str = "NONE",
) -> List[str]:
    """
    Deterministically compute which actions are permitted.
    This is called BEFORE AUREV AI reasons — the LLM can only choose from this list.
    """
    if error_code in ["INSUFFICIENT_FUNDS", "FAILED_FUNDS", "INVALID_DETAILS", "INVALID_PIN", "BANK_UNAVAILABLE", "BANK_DOWN"]:
        return ["DECLINE"]

    if failure_category in ["INSUFFICIENT_FUNDS", "INVALID_PAYMENT_DETAILS", "BANK_SERVER_DOWN"]:
        return ["DECLINE"]

    if recovery_attempt_count >= MAX_RECOVERY_ATTEMPTS:
        logger.info(f"Max recovery attempts ({MAX_RECOVERY_ATTEMPTS}) reached. Only ESCALATE permitted.")
        return ["ESCALATE"]

    if bank_health == "DOWN":
        return ["DECLINE"]

    if money_debited is True:
        # Money left the customer's account — never retry
        return ["RECONCILE", "ESCALATE"]

    if money_debited is None:
        # Unknown — never retry into unknown state
        return ["ESCALATE"]

    # money_debited = False — retry may be safe
    if failure_category in ["NETWORK_TIMEOUT", "TEMPORARY_BANK_ERROR"]:
        return ["RETRY", "ESCALATE"]

    if failure_category in ["GATEWAY_TIMEOUT", "PROCESSING"]:
        return ["WAIT_AND_VERIFY", "ESCALATE"]

    if failure_category == "UNKNOWN_STATUS":
        return ["ESCALATE"]

    if failure_category == "DUPLICATE_RISK":
        return ["RECONCILE"]

    return ["ESCALATE"]


def is_action_permitted(action: str, permitted: List[str]) -> bool:
    return action.upper() in [a.upper() for a in permitted]
