"""OpenAI-compatible image generation endpoint."""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from ...config.settings import settings
from ...database import get_db_manager
from ...database.async_task_manager import get_async_task_manager

router = APIRouter(prefix="/v1", tags=["openai-compat"])


class ImageGenerationRequest(BaseModel):
    """OpenAI-style image generation request."""

    model: str = Field(..., description="模型名称")
    prompt: str = Field(..., description="提示词")
    size: Optional[str] = Field("1024x1024", description="尺寸，例如 1024x1024")
    n: Optional[int] = Field(1, description="生成数量")
    quality: Optional[str] = Field("standard", description="质量")


def _parse_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:].strip() or None
    return None


@router.post("/images/generations")
async def create_image(
    request: ImageGenerationRequest,
    authorization: Optional[str] = Header(None),
):
    """OpenAI-compatible image generation interface."""
    try:
        width, height = 1024, 1024
        if request.size and "x" in request.size:
            w, h = request.size.split("x")
            width, height = int(w), int(h)

        api_key = _parse_bearer_token(authorization)
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing Authorization Bearer API Key.",
            )
        credential_id = None
        db_manager = get_db_manager()
        credential = await db_manager.store_api_credential(
            api_key=api_key,
            provider="relay",
            base_url=settings.relay_base_url,
            user_id="openai-compat",
        )
        credential_id = credential.id

        manager = get_async_task_manager()
        params = {
            "width": width,
            "height": height,
            "n": request.n,
            "quality": request.quality,
            "credential_id": credential_id,
            "relay_base_url": settings.relay_base_url,
        }

        task = await manager.create_task(
            platform=request.model.split("/")[0] if "/" in request.model else "relay",
            model=request.model,
            prompt=request.prompt,
            params=params,
        )

        logger.info(f"OpenAI-compatible request created async task {task.id}")

        return {
            "id": task.id,
            "task_id": task.id,
            "status": task.status,
            "created": int(task.submit_time.timestamp()) if task.submit_time else None,
        }

    except Exception as exc:
        logger.error(f"OpenAI-compatible endpoint error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
