"""
AUREV AI — Agentic Recovery Layer
Uses Gemini for reasoning. Safety Policy Engine gates all actions.
"""
import logging
import json
from typing import Optional, List, Dict
from app.aurev.policies import get_permitted_actions, is_action_permitted
from app.aurev import tools
from app.config.settings import settings

logger = logging.getLogger(__name__)


class AurevAI:
    """
    AUREV AI Agentic Recovery System.

    Decision flow:
    1. Gather payment context (bank health, payment status, verification)
    2. Get ML classification
    3. Compute permitted actions (Safety Policy Engine)
    4. Use Gemini to reason over situation and choose action
    5. Execute chosen action through payment orchestrator
    """

    def __init__(self):
        self.gemini_client = None
        self._init_gemini()

    def _init_gemini(self):
        if settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("AUREV AI: Gemini client initialized")
            except Exception as e:
                logger.warning(f"AUREV AI: Gemini init failed: {e}. Using rule-based fallback.")
        else:
            logger.info("AUREV AI: No Gemini API key. Using rule-based decision making.")

    async def diagnose_and_recover(self, payment, db, event_logger) -> dict:
        """
        Main entry point for payment recovery.
        Returns: dict with action, reasoning, and result.
        """
        logger.info(f"AUREV AI: Starting diagnosis for transaction {payment.transaction_id}")

        await event_logger(payment.id, "recovery_started", "AUREV AI diagnosis initiated", {})

        # Step 1: Gather context
        bank_health_data = await tools.check_bank_health()
        bank_health = bank_health_data.get("status", "UNKNOWN")
        await event_logger(payment.id, "bank_health_checked", f"Bank status: {bank_health}", bank_health_data)

        # Step 2: Get current payment status from bank
        payment_status_data = await tools.get_payment_status(payment.transaction_id)
        await event_logger(
            payment.id, "payment_status_checked",
            f"Bank reports: {payment_status_data.get('status', 'UNKNOWN')}",
            payment_status_data,
        )

        # Step 3: Verify if money moved
        verification = await tools.verify_transaction(payment.transaction_id)
        money_debited = verification.get("money_debited")
        await event_logger(payment.id, "transaction_verified", f"Money debited: {money_debited}", verification)

        # Update payment with verification result
        payment.money_debited = money_debited
        db.commit()

        # Step 4: ML classification
        from app.ml.predictor import predictor
        from app.ml.feature_builder import build_features

        features = build_features(
            payment=payment,
            bank_health=bank_health,
            gateway_health="UP",
            response_time_ms=bank_health_data.get("latency_ms", 0),
            error_code=payment.failure_code or "NONE",
        )
        ml_result = predictor.predict(features)
        failure_category = ml_result["failure_category"]
        confidence = ml_result["confidence"]
        recommended_action = ml_result["recommended_action"]

        await event_logger(
            payment.id, "ml_classified",
            f"ML: {failure_category} ({confidence * 100:.0f}%) → {recommended_action}",
            ml_result,
        )

        # Update payment with ML results
        payment.ml_classification = failure_category
        payment.ml_confidence = confidence
        db.commit()

        # Step 5: Safety Policy Engine — determine what's actually allowed
        permitted_actions = get_permitted_actions(
            failure_category=failure_category,
            money_debited=money_debited,
            bank_health=bank_health,
            recovery_attempt_count=payment.recovery_attempt_count,
            error_code=payment.failure_code or "NONE",
        )
        await event_logger(
            payment.id, "policy_evaluated",
            f"Permitted actions: {permitted_actions}",
            {"permitted": permitted_actions, "failure_category": failure_category},
        )

        # Step 6: Choose action (LLM or rule-based)
        chosen_action, reasoning = await self._choose_action(
            payment=payment,
            failure_category=failure_category,
            confidence=confidence,
            recommended_action=recommended_action,
            permitted_actions=permitted_actions,
            bank_health=bank_health,
            money_debited=money_debited,
        )

        payment.aurev_action = chosen_action
        payment.aurev_reasoning = reasoning
        db.commit()

        await event_logger(
            payment.id, "aurev_decided",
            f"AUREV AI decision: {chosen_action}",
            {"action": chosen_action, "reasoning": reasoning[:200] if reasoning else ""},
        )

        return {
            "action": chosen_action,
            "reasoning": reasoning,
            "failure_category": failure_category,
            "confidence": confidence,
            "permitted_actions": permitted_actions,
            "bank_health": bank_health,
            "money_debited": money_debited,
        }

    async def _choose_action(
        self,
        payment,
        failure_category: str,
        confidence: float,
        recommended_action: str,
        permitted_actions: List[str],
        bank_health: str,
        money_debited: Optional[bool],
    ) -> tuple:
        """Choose recovery action. Uses Gemini if available, else rule-based."""
        if not permitted_actions:
            return "ESCALATE", "No permitted actions available. Escalating for manual review."

        if len(permitted_actions) == 1:
            action = permitted_actions[0]
            return action, f"Only permitted action based on safety policy: {action}"

        if self.gemini_client:
            return await self._gemini_decide(
                payment, failure_category, confidence,
                recommended_action, permitted_actions,
                bank_health, money_debited,
            )

        # Rule-based fallback
        if recommended_action in permitted_actions:
            return (
                recommended_action,
                f"ML recommended {recommended_action} (confidence: {confidence * 100:.0f}%). Action is permitted by safety policy.",
            )
        return permitted_actions[0], f"ML recommendation not permitted. Defaulting to {permitted_actions[0]}."

    async def _gemini_decide(
        self,
        payment,
        failure_category: str,
        confidence: float,
        recommended_action: str,
        permitted_actions: List[str],
        bank_health: str,
        money_debited: Optional[bool],
    ) -> tuple:
        """Use Gemini to reason about the situation and choose an action."""
        prompt = f"""You are AUREV AI, a payment recovery specialist for NIVORA grocery platform.

Payment Situation:
- Transaction ID: {payment.transaction_id}
- Amount: ₹{payment.amount}
- Payment Method: {payment.payment_method}
- Failure Code: {payment.failure_code}
- Bank Health: {bank_health}
- Money Debited from Customer: {money_debited}
- Recovery Attempts So Far: {payment.recovery_attempt_count}
- ML Classification: {failure_category} (confidence: {confidence * 100:.0f}%)
- ML Recommended Action: {recommended_action}

SAFETY CONSTRAINT: You MUST choose from these permitted actions only: {permitted_actions}

Analyze the situation and choose the best action. Respond in JSON:
{{
  "action": "<one of {permitted_actions}>",
  "reasoning": "<brief explanation in 1-2 sentences>"
}}"""

        try:
            response = self.gemini_client.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            action = data.get("action", "").upper()
            reasoning = data.get("reasoning", "")

            if action not in permitted_actions:
                logger.warning(f"Gemini chose non-permitted action '{action}'. Overriding.")
                action = recommended_action if recommended_action in permitted_actions else permitted_actions[0]
                reasoning += f" [Safety override: {action} selected from permitted actions]"

            return action, reasoning
        except Exception as e:
            logger.error(f"Gemini decision failed: {e}. Using rule-based.")
            action = recommended_action if recommended_action in permitted_actions else permitted_actions[0]
            return action, f"Rule-based decision: {action} (ML confidence: {confidence * 100:.0f}%)"


# Singleton
aurev_agent = AurevAI()
