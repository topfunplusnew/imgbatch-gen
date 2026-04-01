"""Helpers for loading backend-managed API configuration."""

from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import select

from ..config.settings import settings
from ..database import SystemConfig, get_db_manager
from .credential_crypto import decrypt_api_key


async def get_relay_config() -> Tuple[str, Optional[str]]:
    """Return the fixed relay base URL plus the configured API key."""

    db_manager = get_db_manager()
    api_key = None

    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == "relay.api_key")
            )
            if config and config.config_value:
                raw_value = config.config_value
                try:
                    api_key = decrypt_api_key(raw_value)
                except Exception as exc:
                    logger.warning(f"Failed to decrypt relay.api_key, using raw value: {exc}")
                    api_key = raw_value.strip()
    except Exception as exc:
        logger.warning(f"Failed to load relay API key from system config: {exc}")

    if not api_key:
        api_key = settings.relay_api_key

    return settings.relay_base_url, api_key


async def get_openai_config() -> Tuple[Optional[str], Optional[str]]:
    """Get OpenAI config with SystemConfig values taking priority."""

    db_manager = get_db_manager()
    base_url = settings.openai_base_url
    api_key = settings.openai_api_key

    try:
        async with db_manager.get_session() as session:
            base_url_config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == "openai.base_url")
            )
            if base_url_config and base_url_config.config_value:
                base_url = base_url_config.config_value.strip()

            api_key_config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == "openai.api_key")
            )
            if api_key_config and api_key_config.config_value:
                try:
                    api_key = decrypt_api_key(api_key_config.config_value)
                except Exception:
                    api_key = api_key_config.config_value.strip()
    except Exception as exc:
        logger.warning(f"Failed to load OpenAI config from system config: {exc}")

    return base_url, api_key


def normalize_openai_base_url(base_url: Optional[str]) -> Optional[str]:
    """Normalize OpenAI-compatible base URLs to end with /v1."""

    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1"):
        normalized += "/v1"
    return normalized


async def resolve_relay_config(preferred_api_key: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """Prefer a request-scoped key and otherwise fall back to system-managed relay config."""

    key = (preferred_api_key or "").strip()
    if key:
        return settings.relay_base_url, key
    return await get_relay_config()


async def require_relay_api_key(preferred_api_key: Optional[str] = None) -> str:
    """Return a usable relay key or raise a clear configuration error."""

    _, api_key = await resolve_relay_config(preferred_api_key)
    key = (api_key or "").strip()
    if key:
        return key
    raise ValueError("系统未配置 relay.api_key，请在 system_configs 表中完成配置")
