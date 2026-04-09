"""LLM adapter factory."""

from app.config import settings
from app.llm.base import LLMAdapter


def get_llm_adapter() -> LLMAdapter:
    """Return the configured LLM adapter instance."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from app.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter()
    elif provider == "anthropic":
        from app.llm.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter()
    elif provider == "ollama":
        from app.llm.ollama_adapter import OllamaAdapter
        return OllamaAdapter()
    else:
        raise ValueError(f"LLM provider '{provider}' is not configured or unsupported")
