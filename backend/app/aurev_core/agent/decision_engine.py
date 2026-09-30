"""
Decision Engine for AUREV.
Orchestrates AI reasoning over assembled context and validates against the deterministic Safety Policy Engine.
"""
from typing import Optional
from agent.context_engine import ContextEngine
from agent.providers.factory import get_ai_provider
from agent.state_manager import StateManager
from safety.policy_engine import SafetyPolicyEngine
from models.decisions import AurevAnalysisResult, AurevReasoningResult
from models.enums import AurevDecision
from models.payment import PaymentAttempt, PaymentSession


class DecisionEngine:
    @classmethod
    def analyze_payment(
        cls,
        payment_id: str,
        session_override: Optional[PaymentSession] = None,
        attempt_override: Optional[PaymentAttempt] = None
    ) -> AurevAnalysisResult:
        # 1. Assemble unified context & ML risk signals
        session, attempt, health, ml_risk, context = ContextEngine.assemble_context(
            payment_id=payment_id,
            session_override=session_override,
            attempt_override=attempt_override
        )

        # 2. AI provider synthesizes reasoning & explanations
        ai_provider = get_ai_provider()
        ai_output = ai_provider.generate_reasoning(context)

        # 3. Deterministic Safety Policy Engine determines final authoritative verdict
        policy_result = SafetyPolicyEngine.evaluate_policy(
            session=session,
            attempt=attempt,
            health=health,
            ml_risk=ml_risk,
            ai_recommendation=ai_output
        )

        # Merge AI explanations into result
        if ai_output.get("explanation"):
            policy_result.reason = f"{policy_result.reason} [AI Note: {ai_output['explanation']}]"

        # 4. Integrate Agent Trace
        agent_trace = list(ai_output.get("agent_trace", []))
        ai_recommendation = str(ai_output.get("recommendation") or ai_output.get("proposed_decision") or "").upper()

        if ai_recommendation == "RETRY" and policy_result.decision != AurevDecision.RETRY:
            agent_trace.append(f"[SAFETY] RETRY DENIED. Enforcing: {policy_result.decision.value}. Reason: {policy_result.reason}")
        else:
            agent_trace.append(f"[SAFETY] Policy Enforced: {policy_result.decision.value} (Finality: {policy_result.finality_state.value}).")

        policy_result.agent_trace = agent_trace

        # Construct AurevReasoningResult if structured data present
        if "agent_status" in ai_output:
            policy_result.reasoning_result = AurevReasoningResult(
                agent_status=ai_output.get("agent_status", "AI_AVAILABLE"),
                observed_evidence=ai_output.get("observed_evidence") or ai_output.get("known") or [],
                evidence_gaps=ai_output.get("evidence_gaps") or ai_output.get("uncertain") or [],
                risk_assessment=ai_output.get("risk_assessment", ""),
                relevant_events=ai_output.get("relevant_events", []),
                requested_tools=ai_output.get("requested_tools", []),
                proposed_decision=policy_result.decision,
                proposed_action=ai_output.get("proposed_action", ""),
                reason_summary=ai_output.get("reason_summary") or ai_output.get("explanation", ""),
                confidence=float(ai_output.get("confidence", 0.95)),
                next_monitoring_step=ai_output.get("next_monitoring_step"),
                agent_trace=agent_trace
            )

        # 5. State Manager updates session and writes immutable audit record
        StateManager.update_session_state(session, policy_result)
        StateManager.record_audit(
            analysis=policy_result,
            context=context,
            ai_reasoning=ai_output.get("explanation", ""),
            financial_safety_mode=health.is_safety_mode_active
        )

        return policy_result
