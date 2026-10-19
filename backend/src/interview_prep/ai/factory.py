import httpx

from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.remote import OllamaProvider, OpenAIProvider
from interview_prep.core.config import Settings


def create_provider(
    settings: Settings, client: httpx.AsyncClient, *, demo: bool = False
) -> AIProvider:
    if demo or settings.ai_provider == "mock":
        return MockAIProvider()
    if settings.ai_provider == "ollama":
        return OllamaProvider(
            client,
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ai_timeout_seconds,
            settings.ai_max_retries,
        )
    if settings.ai_provider == "openai":
        return OpenAIProvider(
            client,
            settings.openai_api_key,
            settings.openai_model,
            settings.ai_timeout_seconds,
            settings.ai_max_retries,
        )
    # Defensive even if a caller bypasses Settings validation.
    raise ValueError("Unsupported AI provider")
