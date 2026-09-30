"""
AUREV Agent - Main Autonomous Safety Brain.
Implements the full agentic loop:
OBSERVE -> UNDERSTAND -> VERIFY -> PROTECT -> ACT -> VERIFY AGAIN -> MONITOR
"""
import logging
from typing import Any, Dict, Optional
from agent.decision_engine import DecisionEngine
from agent.context_engine import ContextEngine
from models.decisions import AurevAnalysisResult
from models.enums import AurevDecision, FinalityState, EventType
from memory.payment_memory import payment_memory
from memory.event_timeline import timeline_store
from tools.action_tools import (
    block_pay_again,
    trigger_reconciliation,
    create_support_case,
    notify_user,
    notify_merchant,
)

logger = logging.getLogger("aurev.agent")


class AurevAgent:
    """
    Continuous Payment Safety Agent.
    Remains attached to payment sessions until trustworthy finality is achieved.
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()

    def process_payment_session(self, payment_id: str) -> AurevAnalysisResult:
        """
        Executes the 7-stage AUREV Agent Loop for a payment:
        1. OBSERVE: Gather multi-source telemetry & timeline.
        2. UNDERSTAND: Extract ML anomaly signals and AI reasoning.
        3. VERIFY: Evaluate cross-source truth (Gateway vs Bank vs Merchant).
        4. PROTECT: Deterministically lock unsafe actions (Block Pay Again, Block Retries).
        5. ACT: Execute authorized safe action tools (Permit, Reconcile, Notify).
        6. VERIFY AGAIN: Re-evaluate state after action execution.
        7. MONITOR: Stay attached until terminal finality.
        """
        # Step 1: OBSERVE & Step 2: UNDERSTAND & Step 3: VERIFY & Step 4: PROTECT
        analysis = self.decision_engine.analyze_payment(payment_id)

        session = payment_memory.get_session_by_payment_id(payment_id)
        if not session:
            return analysis

        # Step 5: ACT (Controlled Action Tools)
        traces = list(analysis.agent_trace)
        if "PAY_AGAIN" in analysis.blocked_actions or analysis.decision == AurevDecision.WAIT:
            block_pay_again(session.order_id, reason="AUREV duplicate protection active")
            if "[AUREV] Pay Again blocked." not in traces:
                traces.append("[AUREV] Pay Again blocked.")

        if "TRIGGER_RECONCILIATION" in analysis.recommended_actions:
            trigger_reconciliation(session.order_id)
            traces.append("[AUREV] Automated reconciliation triggered.")

        if "CREATE_SUPPORT_CASE" in analysis.recommended_actions:
            create_support_case(session.order_id, reason=analysis.reason)
            traces.append("[AUREV] Escalation support case created.")

        if analysis.finality_state == FinalityState.FINAL_SUCCESS:
            notify_user(session.user_id, "Your payment has been successfully confirmed.", level="SUCCESS")
            notify_merchant("MERCHANT-001", session.order_id, status="CONFIRMED")
            if "[AUREV] Payment resolved. Monitoring closed." not in traces:
                traces.append("[AUREV] Payment resolved. Monitoring closed.")
        elif analysis.finality_state == FinalityState.UNKNOWN:
            notify_user(
                session.user_id,
                "Payment confirmation interrupted. Don't pay again yet, we are verifying with your bank.",
                level="WARNING"
            )

        # Step 6: VERIFY AGAIN
        # Re-evaluate in case automated reconciliation modified the state
        re_analysis = self.decision_engine.analyze_payment(payment_id)

        # Step 7: MONITOR
        # Attach continuous monitoring if state is non-final / unknown
        if re_analysis.finality_state not in [FinalityState.FINAL_SUCCESS, FinalityState.FINAL_FAILURE]:
            timeline_store.record_event(
                payment_id=payment_id,
                order_id=session.order_id,
                event_type=EventType.PAYMENT_PROCESSING,
                source="aurev_agent",
                status="MONITORING_ATTACHED",
                metadata={"next_check_at": re_analysis.next_check_at}
            )
            traces.append("[AUREV] Continuous monitoring attached.")
        else:
            if re_analysis.finality_state == FinalityState.FINAL_SUCCESS and "[AUREV] Payment resolved. Monitoring closed." not in traces:
                traces.append("[AUREV] Payment resolved. Monitoring closed.")

        re_analysis.agent_trace = traces
        if re_analysis.reasoning_result:
            re_analysis.reasoning_result.agent_trace = traces

        return re_analysis


# Global Agent instance
aurev_agent = AurevAgent()
