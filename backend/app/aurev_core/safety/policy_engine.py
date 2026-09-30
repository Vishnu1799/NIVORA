"""
Deterministic Safety Policy Engine.
The authoritative final decision-maker for all financial actions in AUREV.
"""
from typing import Any, Dict, List, Optional, Tuple
from config.settings import settings
from models.enums import (
    AurevDecision,
    BankStatus,
    EventType,
    FinalityState,
    GatewayStatus,
    MerchantStatus,
    ReconciliationState,
    RiskLevel,
)
from models.payment import PaymentAttempt, PaymentSession
from models.decisions import AurevAnalysisResult, RecoveryPermit, SystemHealthState
from models.risk import MLRiskResponse
from safety.finality_engine import FinalityEngine
from safety.duplicate_protection import DuplicateProtection
from safety.retry_policy import RetryPolicy
from safety.recovery_permit import RecoveryPermitManager
from memory.event_timeline import timeline_store


class SafetyPolicyEngine:
    """
    Deterministic Safety Policy Engine.
    Enforces invariant rules:
    - Never mark SUCCESS without verified evidence.
    - Never assume timeout means failure.
    - Block retries if customer was debited or prior attempt succeeded.
    - Require single-use Recovery Permit for retries.
    - Enforce Financial Safety Mode when system is degraded.
    """

    @classmethod
    def evaluate_policy(
        cls,
        session: PaymentSession,
        attempt: PaymentAttempt,
        health: SystemHealthState,
        ml_risk: MLRiskResponse,
        ai_recommendation: Optional[Dict[str, Any]] = None
    ) -> AurevAnalysisResult:
        known_evidence: List[str] = []
        uncertain_evidence: List[str] = []
        verification_needed: List[str] = []
        recommended_actions: List[str] = []
        blocked_actions: List[str] = []

        # 1. Compute Finality State deterministically
        finality, finality_reasons = FinalityEngine.evaluate(attempt, session)
        known_evidence.extend(finality_reasons)

        # 2. Duplicate Protection Check
        is_dup, dup_reasons = DuplicateProtection.is_duplicate_risk(session)
        if is_dup:
            blocked_actions.append("PAY_AGAIN")
            blocked_actions.append("INITIATE_NEW_PAYMENT")
            uncertain_evidence.extend(dup_reasons)

        # 3. Check Financial Safety Mode
        if health.is_safety_mode_active or settings.FINANCIAL_SAFETY_MODE_ENABLED:
            blocked_actions.append("NEW_PAYMENT_INITIATION")
            blocked_actions.append("RETRY_PAYMENT")
            uncertain_evidence.append("SYSTEM_ALERT: Financial safety mode active due to platform instability.")

        # Determine Decision based on deterministic rules
        decision: AurevDecision
        reason: str
        permit: Optional[RecoveryPermit] = None
        next_check: Optional[str] = None

        # Rule 1: FINAL_SUCCESS
        if finality == FinalityState.FINAL_SUCCESS:
            decision = AurevDecision.STOP
            reason = "Payment is definitively settled and verified. No further action needed."
            recommended_actions.append("NOTIFY_USER_SUCCESS")
            recommended_actions.append("CONFIRM_MERCHANT_ORDER")
            blocked_actions.append("PAY_AGAIN")
            session.is_pay_again_blocked = True
            session.is_resolved = True

        # Rule 2: UNKNOWN state (e.g. Gateway timeout or missing data)
        elif finality == FinalityState.UNKNOWN:
            decision = AurevDecision.WAIT
            reason = "Payment outcome is UNKNOWN (e.g. timeout). Awaiting bank and gateway verification before taking action."
            blocked_actions.append("PAY_AGAIN")
            blocked_actions.append("AUTHORIZE_RETRY")
            verification_needed.append("REQUEST_BANK_SETTLEMENT_STATUS")
            verification_needed.append("POLL_GATEWAY_TRANSACTION_STATUS")
            recommended_actions.append("BLOCK_PAY_AGAIN")
            recommended_actions.append("SCHEDULE_VERIFICATION_CHECK")
            session.is_pay_again_blocked = True
            next_check = "10_SECONDS"

        # Rule 3: NON_FINAL (Processing / Pending)
        elif finality == FinalityState.NON_FINAL:
            decision = AurevDecision.WAIT
            reason = "Payment is actively processing or pending merchant confirmation. Monitoring in progress."
            blocked_actions.append("PAY_AGAIN")
            blocked_actions.append("AUTHORIZE_RETRY")
            verification_needed.append("WATCH_WEBHOOK_DELIVERY")
            recommended_actions.append("CONTINUE_MONITORING")
            session.is_pay_again_blocked = True
            next_check = "5_SECONDS"

        # Rule 4: CONFLICT (Discrepancy between bank, gateway, merchant or duplicate success)
        elif finality == FinalityState.CONFLICT:
            # Check if customer was debited
            if attempt.customer_debited is True or session.has_debited_attempt():
                decision = AurevDecision.WAIT
                reason = "CONFLICT DETECTED: Bank debited customer but gateway/merchant status is discordant. Triggering automated reconciliation."
                recommended_actions.append("TRIGGER_RECONCILIATION")
                recommended_actions.append("BLOCK_PAY_AGAIN")
                session.reconciliation_state = ReconciliationState.IN_PROGRESS
                verification_needed.append("RECONCILE_BANK_AND_MERCHANT")
                blocked_actions.append("PAY_AGAIN")
                blocked_actions.append("AUTHORIZE_RETRY")
                session.is_pay_again_blocked = True
                next_check = "15_SECONDS"
            else:
                decision = AurevDecision.ESCALATE
                reason = "CONFLICT DETECTED: Irreconcilable payment telemetry. Escalating to support & manual review."
                recommended_actions.append("CREATE_SUPPORT_CASE")
                recommended_actions.append("FREEZE_PAYMENT_STATE")
                blocked_actions.append("PAY_AGAIN")
                session.is_pay_again_blocked = True

        # Rule 5: FINAL_FAILURE
        elif finality == FinalityState.FINAL_FAILURE:
            can_retry, retry_reasons = RetryPolicy.can_retry(
                session=session,
                finality=finality,
                health=health,
                ml_duplicate_risk=ml_risk.duplicate_risk
            )

            if can_retry:
                decision = AurevDecision.RETRY
                reason = "Verified failure with zero debit risk. Conditions allow safe single-use retry."
                permit = RecoveryPermitManager.create_permit(
                    payment_id=attempt.payment_id,
                    order_id=session.order_id,
                    amount=attempt.amount,
                    reason="Definitive failure with verified zero debit risk."
                )
                session.active_recovery_permit = permit
                recommended_actions.append("PERMIT_SINGLE_USE_RETRY")
                recommended_actions.append("ISSUE_RECOVERY_PERMIT")
                session.is_pay_again_blocked = False
            else:
                # If cannot retry due to max attempts or safety mode
                if len(session.attempts) >= settings.MAX_RETRIES_PER_ORDER:
                    decision = AurevDecision.STOP
                    reason = f"Payment failed and reached maximum retry attempts ({settings.MAX_RETRIES_PER_ORDER})."
                    recommended_actions.append("NOTIFY_USER_FAILURE")
                    blocked_actions.append("PAY_AGAIN")
                    session.is_pay_again_blocked = True
                    session.is_resolved = True
                else:
                    decision = AurevDecision.ESCALATE
                    reason = f"Payment failed but retry is blocked by safety policy: {'; '.join(retry_reasons)}"
                    recommended_actions.append("CREATE_SUPPORT_CASE")
                    blocked_actions.append("PAY_AGAIN")
                    session.is_pay_again_blocked = True

        else:
            decision = AurevDecision.ESCALATE
            reason = f"Unrecognized finality state: {finality}."
            recommended_actions.append("CREATE_SUPPORT_CASE")

        # Update session state
        session.finality_state = finality
        session.current_decision = decision

        # Record timeline event
        timeline_store.record_event(
            payment_id=attempt.payment_id,
            order_id=session.order_id,
            event_type=EventType.AUREV_DECISION,
            source="safety_policy_engine",
            status=decision.value,
            attempt_number=attempt.attempt_number,
            metadata={
                "finality": finality.value,
                "decision": decision.value,
                "risk_level": ml_risk.risk_level.value,
                "permit_id": permit.permit_id if permit else None,
                "reason": reason
            }
        )

        return AurevAnalysisResult(
            payment_id=attempt.payment_id,
            order_id=session.order_id,
            finality_state=finality,
            decision=decision,
            risk_level=ml_risk.risk_level,
            confidence=0.98 if finality in [FinalityState.FINAL_SUCCESS, FinalityState.FINAL_FAILURE] else 0.85,
            known_evidence=known_evidence,
            uncertain_evidence=uncertain_evidence,
            verification_needed=verification_needed,
            recommended_actions=recommended_actions,
            blocked_actions=blocked_actions,
            reason=reason,
            next_check_at=next_check,
            permit=permit
        )
