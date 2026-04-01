"""Helpers for startup system configuration seeding."""

from datetime import datetime

from loguru import logger
from sqlalchemy import select

from ..database import SystemConfig


DEFAULT_STARTUP_SYSTEM_CONFIGS = (
    {
        "id": "e1ad6d6f-707b-4ffc-9aa2-e485129c6cfc",
        "config_key": "relay.api_key",
        "config_value": "sk-O5QEXXZyvBKuzCW9K2PZFe56OCRBwd5zLMkNSR3o6H4pdb0G",
        "config_type": "string",
        "category": "api",
        "description": "中转站API Key",
        "is_encrypted": False,
        "is_public": False,
        "updated_at": datetime.fromisoformat("2026-03-24 08:26:42.697384"),
        "updated_by": "3860030b-e0a8-46fd-970e-995e30f7998b",
        "created_at": datetime.fromisoformat("2026-03-22 07:10:31.747191"),
    },
)


async def ensure_startup_system_configs(db_manager) -> None:
    """Insert required system config seeds on startup when they are missing."""

    async with db_manager.get_session() as session:
        inserted_keys: list[str] = []

        for config_data in DEFAULT_STARTUP_SYSTEM_CONFIGS:
            existing = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == config_data["config_key"])
            )
            if existing:
                continue

            session.add(SystemConfig(**config_data))
            inserted_keys.append(config_data["config_key"])

        if not inserted_keys:
            return

        await session.commit()
        logger.info(f"Seeded startup system configs: {', '.join(inserted_keys)}")
