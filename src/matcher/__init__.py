"""Embedding matcher module."""

from .base import BaseMatcher
from .openai_matcher import OpenAIMatcher
from .relay_matcher import RelayMatcher
from .templates import PARAMETER_TEMPLATES, get_template_by_name, get_all_templates

from ..config.providers import ProviderConfig, ProviderType
from ..config.settings import settings


def get_matcher(
    provider: str = None,
    api_key: str = None,
    base_url: str = None,
) -> BaseMatcher:
    """Return a matcher for the configured embedding provider."""
    if provider is None:
        provider = settings.default_embedding_provider

    provider = provider.lower()

    if provider == ProviderType.OPENAI:
        config = ProviderConfig.get_openai_config()
        return OpenAIMatcher(config, api_key=api_key, base_url=base_url)
    if provider == "relay":
        return RelayMatcher(api_key=api_key, base_url=base_url)
    raise ValueError(f"Unsupported embedding provider: {provider}. Supported providers: relay, openai")
