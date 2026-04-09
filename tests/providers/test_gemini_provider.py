import base64

import pytest

from src.models.image import ImageParams
from src.providers.gemini_provider import GeminiProvider


class FakeRelayClient:
    def __init__(self):
        self.last_payload = None

    async def post(self, endpoint, json=None, timeout=None):
        self.last_payload = {
            "endpoint": endpoint,
            "json": json,
            "timeout": timeout,
        }
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": base64.b64encode(b"fake-image").decode("ascii"),
                                }
                            }
                        ]
                    }
                }
            ]
        }

    async def download_image(self, url):
        return b"fake-image"


@pytest.mark.asyncio
async def test_gemini_3_image_payload_includes_image_size_for_square_2k():
    provider = GeminiProvider()
    provider.client = FakeRelayClient()

    params = ImageParams(
        prompt="生成一张海报",
        model="gemini-3.1-flash-image-preview",
        width=2048,
        height=2048,
        quality="2k",
    )

    result = await provider.generate_images(params)

    assert result == [b"fake-image"]
    image_config = provider.client.last_payload["json"]["generationConfig"]["imageConfig"]
    assert image_config["aspectRatio"] == "1:1"
    assert image_config["imageSize"] == "2K"


@pytest.mark.asyncio
async def test_gemini_25_image_payload_does_not_include_image_size():
    provider = GeminiProvider()
    provider.client = FakeRelayClient()

    params = ImageParams(
        prompt="生成一张海报",
        model="gemini-2.5-flash-image",
        width=1024,
        height=1024,
        quality="2k",
    )

    result = await provider.generate_images(params)

    assert result == [b"fake-image"]
    image_config = provider.client.last_payload["json"]["generationConfig"]["imageConfig"]
    assert image_config["aspectRatio"] == "1:1"
    assert "imageSize" not in image_config


@pytest.mark.asyncio
async def test_gemini_3_image_payload_includes_image_size_without_explicit_dimensions():
    provider = GeminiProvider()
    provider.client = FakeRelayClient()

    params = ImageParams(
        prompt="生成一张海报",
        model="gemini-3.1-flash-image-preview",
        width=0,
        height=0,
        quality="2k",
    )

    result = await provider.generate_images(params)

    assert result == [b"fake-image"]
    image_config = provider.client.last_payload["json"]["generationConfig"]["imageConfig"]
    assert image_config["imageSize"] == "2K"
