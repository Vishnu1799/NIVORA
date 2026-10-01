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
    current_status: str = "PROCESSING",
) -> List[str]:
    """
    Deterministically compute permitted actions.
    Core Rule: When certainty is lost, NEVER blindly retry.
    """
    # Definitive failure modes -> DECLINE directly
    if error_code in ["INSUFFICIENT_FUNDS", "FAILED_FUNDS", "INVALID_DETAILS", "INVALID_PIN", "BANK_UNAVAILABLE", "BANK_DOWN"]:
        return ["DECLINE"]

    if failure_category in ["INSUFFICIENT_FUNDS", "INVALID_PAYMENT_DETAILS", "BANK_SERVER_DOWN"]:
        return ["DECLINE"]

    if bank_health == "DOWN":
        return ["DECLINE"]

    # Middle-Stuck / Uncertain state -> WAIT_AND_VERIFY (NO RETRY ALLOWED)
    if current_status == "UNDER_VERIFICATION" or failure_category in ["NETWORK_TIMEOUT", "GATEWAY_TIMEOUT", "UNKNOWN_STATUS", "PROCESSING", "TEMPORARY_BANK_ERROR"]:
        if money_debited is True:
            return ["RECONCILE", "SAFE_RETURN"]
        return ["WAIT_AND_VERIFY", "SAFE_RETURN"]

    if recovery_attempt_count >= MAX_RECOVERY_ATTEMPTS:
        logger.info(f"Max recovery attempts ({MAX_RECOVERY_ATTEMPTS}) reached.")
        return ["SAFE_RETURN", "ESCALATE"]

    return ["WAIT_AND_VERIFY", "SAFE_RETURN"]


def is_action_permitted(action: str, permitted: List[str]) -> bool:
    return action.upper() in [a.upper() for a in permitted]

