"""后台图片资源统一存储辅助函数。"""

from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from loguru import logger
from minio.error import S3Error

from ..config.settings import settings
from ..models.image import ImageParams
from ..storage import get_storage
from ..storage.minio_storage import MinioStorage


def _guess_image_format(filename: Optional[str], content_type: Optional[str] = None) -> str:
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    if suffix == "jpg":
        return "jpeg"
    if suffix in {"jpeg", "png", "webp", "gif", "bmp"}:
        return suffix

    if content_type:
        mime_suffix = content_type.split("/")[-1].lower()
        if mime_suffix == "jpg":
            return "jpeg"
        if mime_suffix in {"jpeg", "png", "webp", "gif", "bmp"}:
            return mime_suffix

    return "png"


def _build_thumbnail_path(asset_path: str) -> str:
    path = Path(asset_path)
    return str(path.with_name(f"{path.stem}_thumb.jpg"))


def _looks_like_local_path(asset_path: str) -> bool:
    candidate = Path(asset_path)
    if candidate.exists() or candidate.is_absolute():
        return True

    storage_root = Path(settings.storage_path)
    try:
        if candidate.as_posix().startswith(storage_root.as_posix().rstrip("/") + "/"):
            return True
    except Exception:
        return False

    return False


def save_image_bytes(
    image_data: bytes,
    *,
    source_name: Optional[str],
    storage_task_id: str,
    prompt: str,
    content_type: Optional[str] = None,
) -> dict:
    """保存图片字节并返回统一的图片信息。"""
    storage = get_storage()
    image_format = _guess_image_format(source_name, content_type)
    result = storage.save_image(
        image_data=image_data,
        task_id=storage_task_id,
        params=ImageParams(prompt=prompt or storage_task_id),
        image_format=image_format,
    )

    return {
        "image_url": result.url,
        "thumbnail_url": result.thumbnail_url,
        "image_path": result.file_path,
    }


async def save_uploaded_image(
    upload_file: UploadFile,
    *,
    storage_task_id: str,
    prompt: str,
) -> dict:
    """保存上传图片并返回统一的图片信息。"""
    image_data = await upload_file.read()
    return save_image_bytes(
        image_data,
        source_name=upload_file.filename,
        storage_task_id=storage_task_id,
        prompt=prompt,
        content_type=upload_file.content_type,
    )


def delete_stored_image_assets(asset_path: Optional[str]) -> None:
    """删除图片及其缩略图，兼容本地与 MinIO 两种存储。"""
    if not asset_path:
        return

    normalized_path = asset_path.strip()
    if not normalized_path:
        return

    candidate_paths = [normalized_path, _build_thumbnail_path(normalized_path)]

    if _looks_like_local_path(normalized_path):
        for path_value in candidate_paths:
            try:
                Path(path_value).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("删除本地图片资源失败 {}: {}", path_value, exc)
        return

    try:
        storage = MinioStorage()
        for object_name in candidate_paths:
            try:
                storage.client.remove_object(storage.bucket_name, object_name.lstrip("/"))
            except S3Error as exc:
                logger.warning("删除 MinIO 图片资源失败 {}: {}", object_name, exc)
    except Exception as exc:
        logger.warning("初始化 MinIO 删除资源失败 {}: {}", normalized_path, exc)
