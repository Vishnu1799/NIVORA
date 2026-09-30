"""
State Manager for AUREV.
Handles state persistence, audit trail recording, and lifecycle transitions.
"""
from typing import Any, Dict, Optional
from memory.payment_memory import payment_memory
from models.decisions import AurevAnalysisResult, AurevAuditRecord
from models.payment import PaymentSession


class StateManager:
    @staticmethod
    def update_session_state(session: PaymentSession, analysis: AurevAnalysisResult):
        session.finality_state = analysis.finality_state
        session.current_decision = analysis.decision
        if "PAY_AGAIN" in analysis.blocked_actions:
            session.is_pay_again_blocked = True
        elif analysis.decision == "RETRY":
            session.is_pay_again_blocked = False

        if analysis.permit:
            session.active_recovery_permit = analysis.permit

        payment_memory.save_session(session)

    @staticmethod
    def record_audit(
        analysis: AurevAnalysisResult,
        context: Dict[str, Any],
        ai_reasoning: str,
        financial_safety_mode: bool = False
    ) -> AurevAuditRecord:
        audit = AurevAuditRecord(
            audit_id=analysis.audit_id,
            payment_id=analysis.payment_id,
            order_id=analysis.order_id,
            observed_evidence=context,
            ml_signals=context.get("ml_signals", []),
            aurev_reasoning=ai_reasoning,
            policy_result={
                "finality": analysis.finality_state.value,
                "decision": analysis.decision.value,
                "confidence": analysis.confidence,
                "recommended_actions": analysis.recommended_actions,
                "blocked_actions": analysis.blocked_actions,
                "permit_id": analysis.permit.permit_id if analysis.permit else None
            },
            decision=analysis.decision,
            actions_taken=analysis.recommended_actions,
            verification_result=analysis.reason,
            financial_safety_mode=financial_safety_mode,
            agent_trace=analysis.agent_trace,
            reasoning_result=analysis.reasoning_result.model_dump() if analysis.reasoning_result else None
        )
        payment_memory.record_audit(audit)
        return audit
