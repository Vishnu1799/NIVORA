"""
Rule-Based AI Provider.
Default zero-latency, offline reasoning engine for AUREV that works without external LLM dependencies.
"""
from typing import Any, Dict, List
from agent.providers.ai_provider import AIProvider


class RuleBasedProvider(AIProvider):
    def generate_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        payment_id = context.get("payment_id", "UNKNOWN")
        gw_status = (context.get("gateway_status") or "UNKNOWN").upper()
        bank_status = (context.get("bank_status") or "UNKNOWN").upper()
        merchant_status = (context.get("merchant_status") or "UNKNOWN").upper()
        customer_debited = context.get("customer_debited")
        merchant_credited = context.get("merchant_credited")
        webhook_received = context.get("webhook_received", False)
        duplicate_risk = context.get("ml_duplicate_risk", 0.0)
        safety_mode = context.get("financial_safety_mode", False)
        attempts_count = context.get("attempts_count", 1)

        known: List[str] = []
        uncertain: List[str] = []
        verify_next: List[str] = []
        recommendation = "WAIT"
        explanation = ""

        # Populate Known Evidence
        known.append(f"Payment ID: {payment_id} (Attempt #{attempts_count})")
        known.append(f"Gateway Status: {gw_status}")
        known.append(f"Bank Status: {bank_status}")
        known.append(f"Merchant Status: {merchant_status}")

        if customer_debited is not None:
            known.append(f"Customer Debited: {customer_debited}")
        if merchant_credited is not None:
            known.append(f"Merchant Credited: {merchant_credited}")
        if webhook_received:
            known.append("Webhook notification confirmed.")

        # Evaluate Reasoning
        # 1. Conflict Check: Gateway failure but bank debit
        if gw_status in ["FAILED", "CANCELLED"] and (customer_debited is True or bank_status == "DEBITED"):
            recommendation = "ESCALATE"
            uncertain.append("CONFLICT: Gateway reports failure but bank reports debit.")
            verify_next.append("Escalate to payment support for manual reconciliation.")
            explanation = "Severe discrepancy between gateway failure and bank debit. Escalation required."

        # 2. Clean Success
        elif gw_status == "SUCCESS" and (customer_debited is True or webhook_received or merchant_credited is True):
            recommendation = "STOP"
            explanation = "Payment successfully verified through gateway capture and debit confirmation. Transaction is complete."

        # 3. Timeout / Unknown
        elif gw_status in ["TIMEOUT", "UNKNOWN"]:
            recommendation = "WAIT"
            uncertain.append("Gateway response timed out; final bank settlement status is currently unknown.")
            verify_next.append("Poll gateway for transaction settlement.")
            verify_next.append("Check bank debit logs for this payment reference.")
            explanation = "Gateway timed out during processing. Must wait and verify bank debit status before allowing any retry."

        # 4. Debited but merchant uncredited
        elif customer_debited is True and merchant_credited is not True:
            recommendation = "WAIT"
            uncertain.append("Customer account was debited, but merchant fulfillment has not completed.")
            verify_next.append("Trigger automated ledger reconciliation.")
            explanation = "Funds were debited from customer but merchant credit is pending. Retrying would cause duplicate charge."

        # 5. Clean Failure
        elif gw_status in ["FAILED", "CANCELLED"] and customer_debited is False and not safety_mode:
            recommendation = "RETRY"
            explanation = "Gateway transaction failed and bank confirms no funds were debited. Safe to request retry permit."

        # 6. Safety Mode
        elif safety_mode:
            recommendation = "WAIT"
            uncertain.append("System is currently in Financial Safety Mode due to platform instability.")
            verify_next.append("Monitor gateway latency and error rates.")
            explanation = "System-level safety mode active. New attempts are paused until platform stabilizes."

        else:
            recommendation = "WAIT"
            uncertain.append("Payment state is non-final.")
            verify_next.append("Continue monitoring payment session.")
            explanation = "Payment is currently processing. Waiting for downstream confirmation."

        return {
            "known": known,
            "uncertain": uncertain,
            "verify_next": verify_next,
            "recommendation": recommendation,
            "explanation": explanation
        }
