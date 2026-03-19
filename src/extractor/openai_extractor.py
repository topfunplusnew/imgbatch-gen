"""OpenAI-backed parameter extractor."""

from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from ..config.providers import ProviderConfig
from ..config.settings import settings
from .base import BaseExtractor
from ..models.image import ImageParams


class OpenAIExtractor(BaseExtractor):
    """Use OpenAI-compatible chat completions to extract image parameters."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        api_key: str = None,
        base_url: str = None,
    ):
        if config is None:
            config = ProviderConfig.get_openai_config()

        self.api_key = (api_key or "").strip()
        self.base_url = base_url or config.get("base_url") or settings.openai_base_url
        self.model = config.get("model") or settings.openai_model

        if not self.api_key:
            raise ValueError("OpenAI extractor requires API key from request.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def extract(self, user_input: str) -> ImageParams:
        prompt = self._build_prompt(user_input)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的参数提取助手，能够从自然语言中提取结构化参数。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            data = self._parse_response(content)
            return self._validate_and_normalize(data)

        except Exception as exc:
            raise ValueError(f"OpenAI parameter extraction failed: {exc}")
