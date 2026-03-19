"""OpenAI-backed embedding matcher."""

from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from ..config.providers import ProviderConfig
from ..config.settings import settings
from .base import BaseMatcher


class OpenAIMatcher(BaseMatcher):
    """Use OpenAI embeddings for prompt matching."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        api_key: str = None,
        base_url: str = None,
    ):
        super().__init__()

        if config is None:
            config = ProviderConfig.get_openai_config()

        self.api_key = (api_key or "").strip()
        self.base_url = base_url or config.get("base_url") or settings.openai_base_url
        self.embedding_model = config.get("embedding_model") or settings.openai_embedding_model

        if not self.api_key:
            raise ValueError("OpenAI matcher requires API key from request.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def get_embedding(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            raise ValueError(f"OpenAI embedding fetch failed: {exc}")
