"""
OpenAI AI Provider for AUREV.
Uses OpenAI Chat Completion API when OPENAI_API_KEY is supplied.
"""
import json
import logging
from typing import Any, Dict
import httpx
from config.settings import settings
from agent.providers.ai_provider import AIProvider
from agent.providers.rule_based_provider import RuleBasedProvider

logger = logging.getLogger("aurev.ai.openai")


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._fallback = RuleBasedProvider()

    def generate_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            logger.info("No OpenAI API key configured. Using RuleBasedProvider fallback.")
            return self._fallback.generate_reasoning(context)

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            prompt = f"""
You are AUREV AI Safety Brain for NIVORA.
Analyze the payment context below and return strict JSON with fields:
- known: list of strings (verified facts)
- uncertain: list of strings (uncertainties/gaps)
- verify_next: list of strings (recommended investigative actions)
- recommendation: "WAIT" | "RETRY" | "STOP" | "ESCALATE"
- explanation: string explaining reasoning

Payment Context:
{json.dumps(context, indent=2)}
"""
            payload = {
                "model": "gpt-4o-mini",
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are AUREV, an expert payment safety AI."},
                    {"role": "user", "content": prompt}
                ]
            }
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                else:
                    logger.warning(f"OpenAI API returned {res.status_code}. Using fallback.")
                    return self._fallback.generate_reasoning(context)
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}. Using fallback.")
            return self._fallback.generate_reasoning(context)
