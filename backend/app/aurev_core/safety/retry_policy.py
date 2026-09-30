"""
Deterministic Retry Policy Engine.
Validates if all strict financial and technical prerequisites are met before authorizing a retry.
"""
from typing import Tuple, List, Optional
from config.settings import settings
from models.payment import PaymentSession
from models.enums import FinalityState, GatewayStatus
from models.decisions import SystemHealthState
from safety.duplicate_protection import DuplicateProtection


class RetryPolicy:
    @staticmethod
    def can_retry(
        session: PaymentSession,
        finality: FinalityState,
        health: SystemHealthState,
        ml_duplicate_risk: float = 0.0
    ) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        # 1. Financial Safety Mode active?
        if health.is_safety_mode_active or settings.FINANCIAL_SAFETY_MODE_ENABLED:
            reasons.append("RETRY_BLOCKED: System is in Financial Safety Mode. New payment attempts are suspended.")
            return False, reasons

        # 2. Gateway Down?
        if health.gateway_status == GatewayStatus.DOWN:
            reasons.append("RETRY_BLOCKED: Payment gateway is DOWN. Retries are blocked to prevent systemic failures.")
            return False, reasons

        # 3. Finality must be FINAL_FAILURE
        if finality != FinalityState.FINAL_FAILURE:
            reasons.append(f"RETRY_BLOCKED: Payment finality state is '{finality.value}', not 'FINAL_FAILURE'.")
            return False, reasons

        # 4. Duplicate protection check
        is_dup, dup_reasons = DuplicateProtection.is_duplicate_risk(session)
        if is_dup:
            reasons.extend(dup_reasons)
            return False, reasons

        # 5. ML duplicate risk threshold
        if ml_duplicate_risk > 0.40:
            reasons.append(f"RETRY_BLOCKED: ML duplicate risk score ({ml_duplicate_risk:.2f}) exceeds safety threshold.")
            return False, reasons

        # 6. Max retry limit check
        attempt_count = len(session.attempts)
        if attempt_count >= settings.MAX_RETRIES_PER_ORDER:
            reasons.append(
                f"RETRY_BLOCKED: Attempt count ({attempt_count}) has reached or exceeded max limit ({settings.MAX_RETRIES_PER_ORDER})."
            )
            return False, reasons

        # 7. Debited status check on any attempt
        if session.has_debited_attempt():
            reasons.append("RETRY_BLOCKED: Bank debit detected on previous attempt.")
            return False, reasons

        reasons.append("RETRY_ALLOWED: All deterministic safety, duplicate protection, and quota conditions verified.")
        return True, reasons
