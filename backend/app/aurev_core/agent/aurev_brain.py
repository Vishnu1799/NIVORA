"""
Backward-compatible AUREV Brain Interface.
Provides the classic ask_aurev() function powered by the production architecture.
"""
import os
import sys

# Ensure parent root is in sys.path when invoked directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Optional
from agent.aurev_agent import aurev_agent
from agent.prompts.system_prompt import AUREV_SYSTEM_PROMPT
from tools.payment_tools import get_payment_state


def ask_aurev(payment_id: str) -> str:
    """
    Analyzes payment situation and returns human-readable and structured reasoning.
    """
    result = aurev_agent.process_payment_session(payment_id)
    
    formatted_output = f"""
==================================================
AUREV ANALYSIS: {result.payment_id}
==================================================
Finality State : {result.finality_state.value}
Decision       : {result.decision.value}
Risk Level     : {result.risk_level.value}
Confidence     : {result.confidence * 100:.1f}%
Audit ID       : {result.audit_id}

[KNOWN EVIDENCE]
{chr(10).join(f"- {item}" for item in result.known_evidence) if result.known_evidence else "None"}

[UNCERTAINTY & GAPS]
{chr(10).join(f"- {item}" for item in result.uncertain_evidence) if result.uncertain_evidence else "None"}

[VERIFICATION NEEDED]
{chr(10).join(f"- {item}" for item in result.verification_needed) if result.verification_needed else "None"}

[BLOCKED ACTIONS]
{chr(10).join(f"- {item}" for item in result.blocked_actions) if result.blocked_actions else "None"}

[RECOMMENDED ACTIONS]
{chr(10).join(f"- {item}" for item in result.recommended_actions) if result.recommended_actions else "None"}

[JUSTIFICATION]
{result.reason}
==================================================
"""
    return formatted_output


if __name__ == "__main__":
    test_ids = ["PAY001", "PAY002", "PAY003", "PAY004", "PAY999"]

    for pid in test_ids:
        print(f"\nAnalyzing: {pid}")
        print(ask_aurev(pid))