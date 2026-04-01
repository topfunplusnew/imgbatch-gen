"""HTTP client for the relay provider."""

from __future__ import annotations

import asyncio
import io
from typing import Any, Dict, Optional, Union

import httpx
from loguru import logger

from ..config.settings import settings


def _raise_relay_error(response: httpx.Response, url: str) -> None:
    """Parse relay errors into friendlier messages."""
    status = response.status_code
    try:
        body = response.json()
        error_msg = body.get("error", {}).get("message", "") or body.get("message", "")
    except Exception:
        error_msg = response.text[:200]

    if status == 422 and error_msg:
        if "violate" in error_msg or "platform rules" in error_msg or "invalid_parameter" in error_msg:
            raise ValueError("Image generation failed because the prompt may contain blocked content.")
        raise ValueError(f"Image generation failed due to invalid parameters: {error_msg}")

    if status == 401:
        raise ValueError("Relay API key is invalid or expired.")
    if status == 429:
        raise ValueError("Relay request rate limit exceeded.")
    if status in {502, 503}:
        raise ValueError(f"Relay service is temporarily unavailable (HTTP {status}): {error_msg[:200]}")

    raise ValueError(f"Relay request failed (HTTP {status}): {error_msg or 'Unknown error'}")


class RelayClient:
    """Minimal async client for the relay provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        retry_base_delay: Optional[float] = None,
        retry_max_delay: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.relay_base_url or "").rstrip("/")
        self.api_key = (api_key or "").strip()
        self._config_loaded = False
        self.retry_base_delay = max(0.0, float(settings.retry_base_delay if retry_base_delay is None else retry_base_delay))
        self.retry_max_delay = max(0.0, float(settings.retry_max_delay if retry_max_delay is None else retry_max_delay))

        # 不再强制要求 base_url 和 api_key，允许后续通过 ensure_config() 加载
        if self.base_url and not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Relay base URL must start with http:// or https://: {self.base_url!r}")

    def _get_retry_delay(self, attempt: int) -> float:
        if self.retry_base_delay <= 0 or self.retry_max_delay <= 0:
            return 0.0
        return min(self.retry_base_delay * (2 ** (attempt - 1)), self.retry_max_delay)

    async def _sleep_before_retry(self, delay: float) -> None:
        if delay > 0:
            await asyncio.sleep(delay)

    def _format_retry_log(self, delay: float, attempt: int, max_attempts: int) -> str:
        if delay <= 0:
            return f"立即重试 (尝试 {attempt}/{max_attempts})"
        return f"{delay}秒后重试 (尝试 {attempt}/{max_attempts})"

    async def ensure_config(self) -> None:
        """
        确保配置已加载（从管理员统一配置获取）
        如果实例化时未提供 api_key，则从 SystemConfig 表读取
        """
        if self._config_loaded:
            return

        if not self.api_key or not self.base_url:
            from ..utils.config_helper import get_relay_config
            base_url, api_key = await get_relay_config()
            if base_url:
                self.base_url = base_url.rstrip("/")
            if api_key:
                self.api_key = api_key

        self._config_loaded = True

        if not self.base_url:
            raise ValueError("Relay base URL is not configured.")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Relay base URL must start with http:// or https://: {self.base_url!r}")
        if not self.api_key:
            raise ValueError("系统未配置 API Key，请联系管理员")

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        if content_type != "multipart/form-data":
            headers["Content-Type"] = content_type
        return headers

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Union[bytes, io.BytesIO, tuple]]] = None,
        timeout: float = 300.0,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        POST请求（带重试）

        Args:
            endpoint: API端点
            data: 表单数据
            json: JSON数据
            files: 文件数据
            timeout: 超时时间（秒）
            max_retries: 最大重试次数（默认2次）
        """
        # 确保配置已加载
        await self.ensure_config()

        url = f"{self.base_url}{endpoint}"
        logger.info(f"-> POST {url} timeout={timeout}")

        max_attempts = max_retries + 1
        for attempt in range(1, max_attempts + 1):
            try:
                timeout_config = httpx.Timeout(connect=30.0, read=timeout, write=30.0, pool=30.0)
                async with httpx.AsyncClient(timeout=timeout_config, follow_redirects=True) as client:
                    logger.info(f"-> files={files is not None}, json={json is not None}, data={data is not None}")
                    if files:
                        headers = self._get_headers("multipart/form-data")
                        processed_files = {}
                        for field_name, file_data in files.items():
                            if isinstance(file_data, tuple):
                                processed_files[field_name] = file_data
                            elif isinstance(file_data, bytes):
                                processed_files[field_name] = (field_name, io.BytesIO(file_data), "image/png")
                            else:
                                if hasattr(file_data, "seek"):
                                    file_data.seek(0)
                                processed_files[field_name] = (field_name, file_data, "image/png")

                        response = await client.post(
                            url,
                            headers=headers,
                            data=data,
                            files=processed_files,
                        )
                    elif json:
                        headers = self._get_headers("application/json")
                        logger.info(f"-> payload: {str(json)[:300]}")
                        response = await client.post(
                            url,
                            headers=headers,
                            json=json,
                        )
                    else:
                        headers = self._get_headers("application/json")
                        response = await client.post(
                            url,
                            headers=headers,
                            json=data,
                        )

                    # 检查HTTP状态码
                    if response.status_code >= 400:
                        # 可重试的状态码：429, 502, 503, 504
                        retryable_statuses = {429, 502, 503, 504}
                        if response.status_code in retryable_statuses and attempt < max_attempts:
                            delay = self._get_retry_delay(attempt)
                            logger.warning(
                                f"Relay返回HTTP {response.status_code}，"
                                f"{self._format_retry_log(delay, attempt, max_attempts)}"
                            )
                            await self._sleep_before_retry(delay)
                            continue

                        logger.error(
                            f"Relay error response HTTP {response.status_code}, body head: {response.text[:500]}"
                        )
                        _raise_relay_error(response, url)

                    raw = response.text
                    if not raw or not raw.strip():
                        raise ValueError(f"Relay returned an empty response (HTTP {response.status_code})")
                    try:
                        return response.json()
                    except Exception:
                        logger.error(f"Relay response is not JSON: {raw[:500]}")
                        raise ValueError(f"Relay returned a non-JSON response: {raw[:200]}")

            except httpx.TimeoutException as exc:
                # 超时错误可重试
                if attempt < max_attempts:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"Relay请求超时，{self._format_retry_log(delay, attempt, max_attempts)}: {str(exc)[:200]}"
                    )
                    await self._sleep_before_retry(delay)
                    continue
                logger.error(f"Relay request timed out: {url}, error: {exc}")
                raise ValueError(f"Relay request timed out: {exc}")

            except (httpx.ConnectError, httpx.NetworkError) as exc:
                # 网络错误可重试
                if attempt < max_attempts:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"Relay网络错误，{self._format_retry_log(delay, attempt, max_attempts)}: {str(exc)[:200]}"
                    )
                    await self._sleep_before_retry(delay)
                    continue
                logger.error(f"Relay request failed: {url}, error: {exc}")
                raise ValueError(f"Relay request failed: {exc}")

            except httpx.HTTPError as exc:
                # 其他HTTP错误不重试
                logger.error(f"Relay request failed: {url}, error: {exc}")
                raise ValueError(f"Relay request failed: {exc}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        GET请求（带重试）

        Args:
            endpoint: API端点
            params: 查询参数
            timeout: 超时时间（秒）
            max_retries: 最大重试次数（默认2次）
        """
        # 确保配置已加载
        await self.ensure_config()

        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        max_attempts = max_retries + 1
        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        url,
                        headers=headers,
                        params=params,
                    )

                    # 检查HTTP状态码
                    if response.status_code >= 400:
                        # 可重试的状态码：429, 502, 503, 504
                        retryable_statuses = {429, 502, 503, 504}
                        if response.status_code in retryable_statuses and attempt < max_attempts:
                            delay = self._get_retry_delay(attempt)
                            logger.warning(
                                f"Relay返回HTTP {response.status_code}，"
                                f"{self._format_retry_log(delay, attempt, max_attempts)}"
                            )
                            await self._sleep_before_retry(delay)
                            continue

                        logger.error(
                            f"Relay error response HTTP {response.status_code}, body head: {response.text[:500]}"
                        )
                        _raise_relay_error(response, url)

                    raw = response.text
                    if not raw or not raw.strip():
                        raise ValueError(f"Relay returned an empty response (HTTP {response.status_code})")
                    try:
                        return response.json()
                    except Exception:
                        logger.error(f"Relay response is not JSON: {raw[:500]}")
                        raise ValueError(f"Relay returned a non-JSON response: {raw[:200]}")

            except httpx.TimeoutException as exc:
                # 超时错误可重试
                if attempt < max_attempts:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"Relay请求超时，{self._format_retry_log(delay, attempt, max_attempts)}: {str(exc)[:200]}"
                    )
                    await self._sleep_before_retry(delay)
                    continue
                logger.error(f"Relay request timed out: {url}, error: {exc}")
                raise ValueError(f"Relay request timed out: {exc}")

            except (httpx.ConnectError, httpx.NetworkError) as exc:
                # 网络错误可重试
                if attempt < max_attempts:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"Relay网络错误，{self._format_retry_log(delay, attempt, max_attempts)}: {str(exc)[:200]}"
                    )
                    await self._sleep_before_retry(delay)
                    continue
                logger.error(f"Relay request failed: {url}, error: {exc}")
                raise ValueError(f"Relay request failed: {exc}")

            except httpx.HTTPError as exc:
                # 其他HTTP错误不重试
                logger.error(f"Relay request failed: {url}, error: {exc}")
                raise ValueError(f"Relay request failed: {exc}")

    async def download_image(self, image_url: str) -> bytes:
        if image_url.startswith("data:image/"):
            import base64

            comma_index = image_url.find(",")
            if comma_index >= 0:
                base64_data = image_url[comma_index + 1 :]
            else:
                base64_data = image_url

            logger.info(f"Decoding base64 image payload (length={len(base64_data)})")
            return base64.b64decode(base64_data)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as exc:
            logger.error(f"Failed to download image: {image_url[:100]}, error: {exc}")
            raise ValueError(f"Failed to download image: {exc}")
