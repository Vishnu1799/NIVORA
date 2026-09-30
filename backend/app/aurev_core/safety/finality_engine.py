"""
Deterministic Payment Finality Engine.
Evaluates multi-source evidence (Gateway, Bank, Merchant, Webhooks) to compute
authoritative financial finality state.
"""
from typing import List, Tuple
from models.payment import PaymentAttempt, PaymentSession
from models.enums import BankStatus, FinalityState, MerchantStatus


class FinalityEngine:
    """
    Evaluates evidence to determine if a payment state is:
    - FINAL_SUCCESS
    - FINAL_FAILURE
    - NON_FINAL
    - UNKNOWN
    - CONFLICT
    """

    @staticmethod
    def evaluate(attempt: PaymentAttempt, session: PaymentSession) -> Tuple[FinalityState, List[str]]:
        reasons: List[str] = []
        gw_status = (attempt.gateway_status or "UNKNOWN").upper()
        bank_status = attempt.bank_status
        merchant_status = attempt.merchant_status
        debited = attempt.customer_debited
        credited = attempt.merchant_credited

        # Check for multiple successful attempts on same order (Duplicate Conflict)
        successful_attempts = [
            a for a in session.attempts 
            if a.gateway_status == "SUCCESS" or (a.customer_debited is True and a.merchant_credited is True)
        ]
        if len(successful_attempts) > 1:
            reasons.append(f"CONFLICT: Multiple attempts ({len(successful_attempts)}) succeeded on order {session.order_id}.")
            return FinalityState.CONFLICT, reasons

        # 1. CONFLICT SCENARIOS
        # Discrepancy: Gateway failed but bank debited customer
        if gw_status in ["FAILED", "CANCELLED", "TIMEOUT"] and (debited is True or bank_status == BankStatus.DEBITED):
            reasons.append("CONFLICT: Gateway reported failure/timeout, but customer bank account was DEBITED.")
            return FinalityState.CONFLICT, reasons

        # Discrepancy: Gateway success but bank failed / not debited
        if gw_status == "SUCCESS" and (debited is False or bank_status in [BankStatus.FAILED, BankStatus.NOT_DEBITED]):
            reasons.append("CONFLICT: Gateway reported SUCCESS, but bank reported NOT_DEBITED/FAILED.")
            return FinalityState.CONFLICT, reasons

        # Discrepancy: Customer debited but merchant marked failed
        if debited is True and merchant_status == MerchantStatus.FAILED:
            reasons.append("CONFLICT: Customer was debited, but merchant order failed to credit.")
            return FinalityState.CONFLICT, reasons

        # 2. FINAL_SUCCESS SCENARIOS
        # Both customer debited and merchant confirmed
        if (debited is True or bank_status == BankStatus.DEBITED) and (credited is True or merchant_status == MerchantStatus.CONFIRMED):
            reasons.append("FINAL_SUCCESS: Customer bank debit and merchant order fulfillment confirmed.")
            return FinalityState.FINAL_SUCCESS, reasons

        # Gateway success with webhook received and no bank debit negation
        if gw_status == "SUCCESS" and debited is not False and merchant_status != MerchantStatus.FAILED:
            if attempt.webhook_received or credited is True or merchant_status == MerchantStatus.CONFIRMED:
                reasons.append("FINAL_SUCCESS: Gateway capture and webhook/merchant verification succeeded.")
                return FinalityState.FINAL_SUCCESS, reasons
            else:
                # Gateway success but merchant confirmation pending
                reasons.append("NON_FINAL: Gateway succeeded, but merchant confirmation is pending.")
                return FinalityState.NON_FINAL, reasons

        # 3. FINAL_FAILURE SCENARIOS
        if gw_status in ["FAILED", "CANCELLED"] and (debited is False or bank_status in [BankStatus.FAILED, BankStatus.NOT_DEBITED]):
            reasons.append("FINAL_FAILURE: Verified failure with no customer debit or bank charge.")
            return FinalityState.FINAL_FAILURE, reasons

        # 4. UNKNOWN SCENARIOS
        if gw_status in ["TIMEOUT", "UNKNOWN"]:
            if debited is None and bank_status == BankStatus.UNKNOWN:
                reasons.append("UNKNOWN: Gateway timeout/unreachable; bank settlement status is currently unknown.")
                return FinalityState.UNKNOWN, reasons

        # 5. NON_FINAL SCENARIOS
        if gw_status in ["PROCESSING", "INITIATED", "PENDING"] or bank_status == BankStatus.PENDING:
            reasons.append("NON_FINAL: Transaction is actively processing in the payment pipeline.")
            return FinalityState.NON_FINAL, reasons

        # 6. Customer debited but merchant confirmation missing
        if debited is True and merchant_status in [MerchantStatus.UNKNOWN, MerchantStatus.PENDING]:
            reasons.append("NON_FINAL: Customer debited, awaiting merchant order reconciliation.")
            return FinalityState.NON_FINAL, reasons

        # Fallback to UNKNOWN
        reasons.append(f"UNKNOWN: Inconclusive state from Gateway={gw_status}, Bank={bank_status}, Merchant={merchant_status}.")
        return FinalityState.UNKNOWN, reasons
