"""配置读取辅助函数

从 SystemConfig 表读取配置，fallback 到 settings。
用于实现管理员统一配置中转站 API。
"""

from typing import Optional, Tuple
from loguru import logger
from sqlalchemy import select

from ..config.settings import settings
from ..database import get_db_manager, SystemConfig
from .credential_crypto import decrypt_api_key


async def get_relay_config() -> Tuple[str, Optional[str]]:
    """
    获取中转站配置 (base_url, api_key)
    优先从 SystemConfig 表读取，fallback 到 settings

    Returns:
        tuple: (base_url, api_key) - base_url 必有值，api_key 可能为 None
    """
    db_manager = get_db_manager()
    base_url = settings.relay_base_url
    api_key = None

    try:
        async with db_manager.get_session() as session:
            # 获取 base_url
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == "relay.base_url")
            )
            config = result.scalar_one_or_none()
            if config and config.config_value:
                base_url = config.config_value.strip()
                logger.debug(f"从数据库读取 relay.base_url: {base_url}")

            # 获取 api_key
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == "relay.api_key")
            )
            config = result.scalar_one_or_none()
            if config and config.config_value:
                raw_value = config.config_value
                logger.debug(f"数据库中 relay.api_key 原始值 (前50字符): {raw_value[:50] if raw_value else 'None'}...")
                try:
                    api_key = decrypt_api_key(raw_value)
                    # 脱敏日志
                    masked = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
                    logger.info(f"从数据库解密 relay.api_key 成功: {masked}, 长度={len(api_key)}")
                except Exception as e:
                    logger.warning(f"解密 relay.api_key 失败: {e}")
                    # 如果解密失败，尝试直接使用原值
                    api_key = raw_value.strip()
                    masked = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
                    logger.info(f"使用原值作为 relay.api_key: {masked}, 长度={len(api_key)}")
    except Exception as e:
        logger.warning(f"从数据库读取中转站配置失败: {e}")

    # Fallback 到 settings
    if not api_key:
        api_key = settings.relay_api_key
        if api_key:
            logger.debug("使用 settings 中的 relay_api_key")

    return base_url, api_key


async def get_openai_config() -> Tuple[Optional[str], Optional[str]]:
    """
    获取 OpenAI 配置 (base_url, api_key)
    优先从 SystemConfig 表读取，fallback 到 settings

    Returns:
        tuple: (base_url, api_key) - 都可能为 None
    """
    db_manager = get_db_manager()
    base_url = settings.openai_base_url
    api_key = settings.openai_api_key

    try:
        async with db_manager.get_session() as session:
            # 获取 base_url
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == "openai.base_url")
            )
            config = result.scalar_one_or_none()
            if config and config.config_value:
                base_url = config.config_value.strip()

            # 获取 api_key
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == "openai.api_key")
            )
            config = result.scalar_one_or_none()
            if config and config.config_value:
                try:
                    api_key = decrypt_api_key(config.config_value)
                except Exception:
                    api_key = config.config_value.strip()
    except Exception as e:
        logger.warning(f"从数据库读取 OpenAI 配置失败: {e}")

    return base_url, api_key


def normalize_openai_base_url(base_url: Optional[str]) -> Optional[str]:
    """规范化 OpenAI Base URL，确保以 /v1 结尾"""
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1"):
        normalized += "/v1"
    return normalized