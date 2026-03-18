"""LLM parameter extraction module."""

from .base import BaseExtractor
from .openai_extractor import OpenAIExtractor
from .relay_extractor import RelayExtractor
from .schema import IMAGE_PARAMS_SCHEMA

from ..config.providers import ProviderConfig, ProviderType
from ..config.settings import settings


def get_extractor(
    provider: str = None,
    api_key: str = None,
    base_url: str = None,
) -> BaseExtractor:
    """Return an extractor for the configured provider."""
    if provider is None:
        provider = settings.default_llm_provider

    provider = provider.lower()

    if provider == ProviderType.OPENAI:
        config = ProviderConfig.get_openai_config()
        return OpenAIExtractor(config, api_key=api_key, base_url=base_url)
    if provider == "relay":
        return RelayExtractor(api_key=api_key, base_url=base_url)
    raise ValueError(f"Unsupported LLM provider: {provider}")
