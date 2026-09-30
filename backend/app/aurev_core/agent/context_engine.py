"""
Context Engine for AUREV.
Aggregates and structures multi-source evidence: payment state, attempt history,
bank settlement, merchant confirmation, timeline events, ML signals, and platform health.
"""
from typing import Any, Dict, Optional, Tuple
from memory.payment_memory import payment_memory
from memory.event_timeline import timeline_store
from models.payment import PaymentAttempt, PaymentSession
from models.risk import MLRiskRequest, MLRiskResponse
from models.decisions import SystemHealthState
from ml.factory import get_ml_provider
from tools.observation_tools import get_server_health, _system_health


class ContextEngine:
    @classmethod
    def assemble_context(
        cls,
        payment_id: str,
        session_override: Optional[PaymentSession] = None,
        attempt_override: Optional[PaymentAttempt] = None
    ) -> Tuple[PaymentSession, PaymentAttempt, SystemHealthState, MLRiskResponse, Dict[str, Any]]:
        # 1. Resolve Session and Attempt
        session = session_override or payment_memory.get_session_by_payment_id(payment_id)
        if not session:
            # Create transient session for untracked payment
            session = payment_memory.create_session(
                order_id=f"ORD-EXT-{payment_id}",
                payment_id=payment_id,
                amount=1000.0,
                gateway_status="UNKNOWN"
            )

        attempt = attempt_override or session.get_attempt(payment_id) or session.get_latest_attempt()
        if not attempt:
            attempt = PaymentAttempt(
                attempt_number=1,
                payment_id=payment_id,
                transaction_id=f"TXN-{payment_id}",
                amount=session.amount,
                gateway_status="UNKNOWN"
            )

        # 2. Get Platform Health
        health = _system_health

        # 3. Query ML Risk Signals
        ml_provider = get_ml_provider()
        ml_req = MLRiskRequest(
            payment_id=payment_id,
            order_id=session.order_id,
            amount=attempt.amount,
            gateway=attempt.gateway,
            attempt_number=attempt.attempt_number,
            gateway_status=attempt.gateway_status,
            customer_debited=attempt.customer_debited,
            merchant_status=attempt.merchant_status.value,
            bank_status=attempt.bank_status.value,
            previous_attempts=len(session.attempts) - 1,
            same_order_previous_success=session.has_successful_attempt(),
            server_latency=health.avg_latency_ms,
            server_error_rate=health.error_rate
        )
        ml_risk = ml_provider.analyze_payment(ml_req)

        # 4. Compact Event Timeline (Prioritize critical milestones + recent events)
        events = timeline_store.get_events_for_payment(payment_id)
        critical_event_types = {"PAYMENT_INITIATED", "BANK_DEBIT", "AUREV_DECISION", "RECOVERY_PERMIT_ISSUED", "RECONCILIATION_COMPLETED"}
        milestones = [
            f"{e.timestamp.strftime('%H:%M:%S')} - {e.event_type.value}: {e.status}"
            for e in events if e.event_type.value in critical_event_types
        ]
        recent = [
            f"{e.timestamp.strftime('%H:%M:%S')} - {e.event_type.value} ({e.source}): {e.status}"
            for e in events[-5:]
        ]
        # Deduplicate while preserving order
        compact_timeline = list(dict.fromkeys(milestones + recent))

        # 5. Build Unified Context Dictionary
        permit_info = None
        if session.active_recovery_permit:
            permit_info = {
                "permit_id": session.active_recovery_permit.permit_id,
                "status": session.active_recovery_permit.status.value,
                "amount": session.active_recovery_permit.amount,
                "single_use": session.active_recovery_permit.single_use
            }

        context_dict = {
            "payment_id": payment_id,
            "order_id": session.order_id,
            "amount": attempt.amount,
            "currency": attempt.currency,
            "payment_method": attempt.payment_method,
            "gateway": attempt.gateway,
            "current_state": attempt.gateway_status,
            "gateway_status": attempt.gateway_status,
            "finality_state": session.finality_state.value,
            "attempt_number": attempt.attempt_number,
            "previous_attempts": len(session.attempts) - 1,
            "attempts_count": len(session.attempts),
            "bank_status": attempt.bank_status.value,
            "merchant_status": attempt.merchant_status.value,
            "customer_debited": attempt.customer_debited,
            "customer_debit_state": attempt.customer_debited,
            "merchant_credited": attempt.merchant_credited,
            "webhook_received": attempt.webhook_received,
            "webhook_status": {
                "received": attempt.webhook_received,
                "delay_ms": attempt.webhook_delay_ms
            },
            "server_health": {
                "status": health.server_status.value,
                "gateway_status": health.gateway_status.value,
                "latency_ms": health.avg_latency_ms,
                "error_rate": health.error_rate,
                "safety_mode": health.is_safety_mode_active
            },
            "is_pay_again_blocked": session.is_pay_again_blocked,
            "reconciliation_state": session.reconciliation_state.value,
            "same_order_previous_success": session.has_successful_attempt(),
            "financial_safety_mode": health.is_safety_mode_active,
            "system_safety_mode": health.is_safety_mode_active,
            "recovery_permit_state": permit_info,
            "idempotency_state": {
                "is_resolved": session.is_resolved,
                "pay_again_blocked": session.is_pay_again_blocked,
                "attempts_count": len(session.attempts)
            },
            "ml_anomaly_score": ml_risk.anomaly_score,
            "ml_duplicate_risk": ml_risk.duplicate_risk,
            "ml_failure_risk": ml_risk.failure_risk,
            "ml_signals": ml_risk.signals,
            "recent_events": compact_timeline,
            "payment_timeline": compact_timeline
        }

        return session, attempt, health, ml_risk, context_dict
