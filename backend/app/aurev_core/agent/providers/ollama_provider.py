"""
Ollama AI Provider for local LLM inference (optional).
"""
import json
import logging
from typing import Any, Dict
from config.settings import settings
from agent.providers.ai_provider import AIProvider
from agent.providers.rule_based_provider import RuleBasedProvider

logger = logging.getLogger("aurev.ai.ollama")


class OllamaProvider(AIProvider):
    def __init__(self, host: str = "", model: str = ""):
        self.host = host or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL
        self._fallback = RuleBasedProvider()

    def generate_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from ollama import chat
            prompt = f"""
You are AUREV, the Agentic AI safety brain of NIVORA.
Analyze the payment situation and return JSON with keys:
known (list), uncertain (list), verify_next (list), recommendation (WAIT|RETRY|STOP|ESCALATE), explanation (str).

Context:
{json.dumps(context, indent=2)}
"""
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are AUREV payment safety brain. Return JSON only."},
                    {"role": "user", "content": prompt}
                ]
            )
            raw = response.message.content
            # Try to parse json from output
            start_idx = raw.find("{")
            end_idx = raw.rfind("}")
            if start_idx != -1 and end_idx != -1:
                return json.loads(raw[start_idx:end_idx + 1])
            return self._fallback.generate_reasoning(context)
        except Exception as e:
            logger.warning(f"Ollama execution failed: {e}. Falling back to RuleBasedProvider.")
            return self._fallback.generate_reasoning(context)
