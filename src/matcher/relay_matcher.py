"""Relay-backed embedding matcher."""

from typing import Any, Dict, List, Optional

from loguru import logger
from openai import AsyncOpenAI

from ..config.settings import settings
from .base import BaseMatcher


class RelayMatcher(BaseMatcher):
    """Use the relay endpoint for embedding generation."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        api_key: str = None,
        base_url: str = None,
    ):
        super().__init__()

        config = config or {}
        self.base_url = base_url or config.get("base_url") or settings.relay_base_url
        self.api_key = (api_key or "").strip()
        self.embedding_model = config.get("embedding_model") or settings.openai_embedding_model

        if not self.api_key:
            raise ValueError("Relay matcher requires API key from request.")

        client_base_url = (self.base_url or "").rstrip("/")
        if client_base_url and not client_base_url.endswith("/v1"):
            client_base_url = f"{client_base_url}/v1"

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=client_base_url or None,
        )

    async def get_embedding(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            logger.info(f"Embedding response type: {type(response)}, value: {response}")
            if isinstance(response, str):
                raise ValueError(f"API returned a string instead of an object: {response}")
            return response.data[0].embedding
        except Exception as exc:
            raise ValueError(f"Relay embedding fetch failed: {exc}")
