"""
Duplicate Payment Protection Engine.
Strictly prevents double debiting and redundant charges.
"""
from typing import Tuple, List
from models.payment import PaymentSession
from models.enums import BankStatus


class DuplicateProtection:
    """
    Evaluates session history and evidence to determine if a new payment attempt
    or retry poses a duplicate charge risk.
    """

    @staticmethod
    def is_duplicate_risk(session: PaymentSession) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        # 1. Any prior attempt already succeeded
        if session.has_successful_attempt():
            reasons.append(f"DUPLICATE_RISK: Order {session.order_id} already has a confirmed successful payment attempt.")
            return True, reasons

        # 2. Any prior attempt has customer debited
        for att in session.attempts:
            if att.customer_debited is True or att.bank_status == BankStatus.DEBITED:
                reasons.append(
                    f"DUPLICATE_RISK: Attempt {att.attempt_number} ({att.payment_id}) has customer debited. "
                    "Cannot initiate another payment until this is resolved."
                )
                return True, reasons

        # 3. Any active attempt is in UNKNOWN or PROCESSING state
        for att in session.attempts:
            gw = (att.gateway_status or "").upper()
            if gw in ["PROCESSING", "INITIATED", "PENDING", "UNKNOWN", "TIMEOUT"] and not att.is_terminal:
                reasons.append(
                    f"DUPLICATE_RISK: Attempt {att.attempt_number} ({att.payment_id}) is in non-terminal state '{gw}'. "
                    "Must verify existing attempt before initiating a new charge."
                )
                return True, reasons

        return False, ["No duplicate payment risk detected."]
