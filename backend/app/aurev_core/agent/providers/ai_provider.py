"""
Abstract Base Class for AI Reasoning Providers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProvider(ABC):
    @abstractmethod
    def generate_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes payment context, telemetry, and evidence into structured reasoning.
        Returns:
            {
                "known": [...],
                "uncertain": [...],
                "verify_next": [...],
                "recommendation": "WAIT" | "RETRY" | "STOP" | "ESCALATE",
                "explanation": "..."
            }
        """
        pass
