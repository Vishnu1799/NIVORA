"""
Factory for creating AI Reasoning Providers.
"""
from config.settings import settings
from agent.providers.ai_provider import AIProvider
from agent.providers.rule_based_provider import RuleBasedProvider
from agent.providers.gemini_provider import GeminiProvider
from agent.providers.openai_provider import OpenAIProvider
from agent.providers.ollama_provider import OllamaProvider


def get_ai_provider() -> AIProvider:
    provider_name = settings.AI_PROVIDER.lower()
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "ollama":
        return OllamaProvider()
    return RuleBasedProvider()
