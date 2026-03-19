"""文件管理接口"""

import os
import uuid
import shutil
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel, Field
from minio import Minio
from ...database import get_db_manager
from ...config.settings import settings

router = APIRouter(prefix="/api/v1/files", tags=["files"])

# ==================== MinIO 客户端配置 ====================

class MinIOClient:
    """MinIO客户端单例"""
    _instance = None

    @classmethod
    def get_instance(cls):
        """获取MinIO客户端实例"""
        if cls._instance is None:
            try:
                cls._instance = Minio(
                    endpoint=settings.minio_endpoint,
                    access_key=settings.minio_access_key,
                    secret_key=settings.minio_secret_key,
                    secure=settings.minio_secure
                )
                logger.info(f"MinIO客户端初始化成功: {settings.minio_endpoint}")
            except Exception as e:
                logger.error(f"MinIO客户端初始化失败: {e}")
                cls._instance = None
        return cls._instance

    @classmethod
    def reset(cls):
        """重置客户端实例（用于测试）"""
        cls._instance = None


# ==================== 请求/响应模型 ====================

class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: int = Field(..., description="文件ID")
    original_filename: str = Field(..., description="原始文件名")
    file_url: str = Field(..., description="文件访问URL")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件MIME类型")
    file_extension: str = Field(..., description="文件扩展名")
    category: str = Field(..., description="文件分类")
    uploaded_at: datetime = Field(..., description="上传时间")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="原始文件名")
    url: str = Field(..., description="文件访问URL")
    size: int = Field(..., description="文件大小（字节）")
    status: str = Field(..., description="上传状态")


# ==================== 工具函数 ====================

def get_file_category(filename: str, file_type: str) -> str:
    """根据文件名和类型确定文件分类"""
    extension = os.path.splitext(filename)[1].lower()

    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md']

    if extension in image_extensions or file_type.startswith('image/'):
        return 'image'
    elif extension in document_extensions or file_type.startswith('application/'):
        return 'document'
    else:
        return 'other'


def get_safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 获取扩展名
    extension = os.path.splitext(filename)[1]

    # 生成唯一文件名
    unique_id = str(uuid.uuid4())
    timestamp = str(int(datetime.now().timestamp()))

    # 组合文件名
    safe_filename = f"{timestamp}_{unique_id}{extension}"

    return safe_filename


def ensure_upload_directory() -> str:
    """确保上传目录存在"""
    upload_dir = getattr(settings, 'upload_dir', 'uploads')
    if not os.path.isabs(upload_dir):
        # 如果是相对路径，基于项目根目录
        upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', upload_dir)

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"创建上传目录: {upload_dir}")

    return upload_dir


def get_file_url(stored_filename: str) -> str:
    """生成文件访问URL"""
    upload_dir = getattr(settings, 'upload_dir', 'uploads')

    if os.path.isabs(upload_dir):
        relative_path = os.path.basename(upload_dir)
        return f"/api/v1/files/download/{stored_filename}"
    else:
        return f"/api/v1/files/download/{stored_filename}"


def normalize_file_url(file_url: str) -> str:
    """标准化文件URL，如果是MinIO URL则直接返回，否则构建完整URL"""
    if file_url.startswith('http://') or file_url.startswith('https://'):
        return file_url
    return file_url


# ==================== 路由 ====================

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    message_id: Optional[int] = None,
    minio_path: Optional[str] = None  # 新增：MinIO路径参数
):
    """
    上传单个文件

    支持两种上传方式:
    1. 直接上传文件内容（原有方式）
    2. MinIO路径上传（传入minio_path，后端从MinIO读取）

    支持的文件类型:
    - 图片: JPG, JPEG, PNG, GIF, WebP, BMP, SVG
    - 文档: PDF, DOC, DOCX, TXT, MD

    参数:
    - conversation_id: 可选，关联的对话ID
    - message_id: 可选，关联的消息ID
    - minio_path: 可选，MinIO中的文件路径（格式：minio:filename）
    """
    try:
        # 如果传入了MinIO路径，直接使用该路径
        if minio_path:
            if not minio_path.startswith('minio:'):
                raise HTTPException(
                    status_code=400,
                    detail="MinIO路径格式错误，应为 minio:filename"
                )

            # 从MinIO路径提取文件名
            minio_filename = minio_path.split('minio:')[1]

            # 验证MinIO路径中的文件是否存在
            minio_client = MinIOClient.get_instance()
            try:
                bucket_name = settings.minio_bucket_name or 'images'
                minio_client.stat_object(
                    bucket=bucket_name,
                    object_name=minio_filename
                )
                logger.info(f"MinIO文件验证成功: {minio_filename}")
            except Exception as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"MinIO中未找到文件: {minio_filename}"
                )

            # 生成文件访问URL
            file_url = _build_public_file_url(request, bucket_name, minio_filename)

            # 保存到数据库（使用MinIO路径）
            db_manager = get_db_manager()
            file_extension = os.path.splitext(minio_filename)[1]

            uploaded_file = await db_manager.create_uploaded_file(
                original_filename=minio_filename,
                stored_filename=minio_filename,  # MinIO文件名作为存储文件名
                file_path=minio_path,  # 保存MinIO路径
                file_url=file_url,
                file_size=0,  # 暂时设为0，实际文件在MinIO中
                file_type='application/octet-stream',
                file_extension=file_extension,
                category=get_file_category(minio_filename, 'application/octet-stream'),
                conversation_id=conversation_id,
                message_id=message_id,
                is_public=False,
                minio_path=minio_path  # 标记为MinIO文件
            )

            logger.info(f"MinIO路径注册成功: {minio_path}")

            return FileUploadResponse(
                file_id=str(uploaded_file.id),
                filename=minio_filename,
                url=file_url,
                size=uploaded_file.file_size or 0,
                status="uploaded"
            )

        # 原有的直接上传方式
        else:
            # 读取文件内容
            file_content = await file.read()

            # 获取文件信息
            original_filename = file.filename or "unnamed"
            file_size = len(file_content)
            file_type = file.content_type or "application/octet-stream"

            # 支持任意大小的文件，不再限制
            # 如果需要限制，可以设置 max_size 值
            # max_size = 50 * 1024 * 1024  # 50MB
            # if file_size > max_size:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"文件大小超过限制，最大支持 {max_size // (1024 * 1024)}MB"
            #     )

            # 确定文件分类
            category = get_file_category(original_filename, file_type)

            # 生成安全的文件名
            stored_filename = get_safe_filename(original_filename)

            # 确保上传目录存在
            upload_dir = ensure_upload_directory()
            file_path = os.path.join(upload_dir, stored_filename)

            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # 生成文件访问URL
            file_url = get_file_url(stored_filename)

            # 保存到数据库
            db_manager = get_db_manager()
            file_extension = os.path.splitext(original_filename)[1]

            uploaded_file = await db_manager.create_uploaded_file(
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_url=file_url,
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                category=category,
                conversation_id=conversation_id,
                message_id=message_id,
                is_public=False
            )

            logger.info(f"文件上传成功: {original_filename} -> {stored_filename}")

            return FileUploadResponse(
                file_id=str(uploaded_file.id),
                filename=original_filename,
                url=file_url,
                size=file_size,
                status="uploaded"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload/batch")
async def upload_files_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    conversation_id: Optional[str] = None
):
    """
    批量上传文件
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="没有选择文件")

        if len(files) > 20:  # 限制最多20个文件
            raise HTTPException(
                status_code=400,
                detail="批量上传最多支持20个文件"
            )

        results = []
        upload_errors = []

        for file in files:
            try:
                # 上传单个文件
                result = await upload_file(request, file, conversation_id)
                results.append(result)
            except Exception as e:
                logger.warning(f"文件 {file.filename} 上传失败: {str(e)}")
                upload_errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        return {
            "total": len(files),
            "success": len(results),
            "failed": len(upload_errors),
            "files": results,
            "errors": upload_errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    下载文件
    """
    try:
        upload_dir = ensure_upload_directory()
        file_path = os.path.join(upload_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


import httpx as _httpx
from fastapi.responses import StreamingResponse as _StreamingResponse
from urllib.parse import unquote, urlsplit, urlunsplit


def _get_public_base_url(request: Request) -> str:
    """Resolve the externally reachable base URL for browser-facing links."""
    origin = request.headers.get("origin")
    if origin and origin.startswith(("http://", "https://")):
        return origin.rstrip("/")

    explicit_base = getattr(settings, "public_base_url", None)
    if explicit_base:
        return explicit_base.rstrip("/")

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}".rstrip("/")

    return str(request.base_url).rstrip("/")


def _build_public_file_url(request: Request, bucket: str, object_name: str) -> str:
    """Build a browser-accessible absolute URL for a MinIO object."""
    object_path = object_name.lstrip("/")
    prefix = settings.minio_url_prefix

    if prefix:
        normalized_prefix = prefix.rstrip("/")
        if normalized_prefix.startswith(("http://", "https://")):
            return f"{normalized_prefix}/{object_path}"
        return f"{_get_public_base_url(request)}{normalized_prefix}/{object_path}"

    return f"{_get_public_base_url(request)}/{bucket}/{object_path}"


def _rewrite_presigned_url_for_browser(request: Request, presigned_url: str) -> str:
    """Swap the internal MinIO host with the public app host, preserving path and signature."""
    public_base = urlsplit(_get_public_base_url(request))
    signed_url = urlsplit(presigned_url)
    return urlunsplit((
        public_base.scheme or signed_url.scheme,
        public_base.netloc,
        signed_url.path,
        signed_url.query,
        "",
    ))


@router.post("/minio/presigned-url")
async def get_minio_presigned_url(request: Request, filename: str):
    """获取MinIO预签名上传URL，支持前端直传"""
    try:
        minio_client = MinIOClient.get_instance()
        if not minio_client:
            raise HTTPException(status_code=500, detail="MinIO客户端未初始化")

        bucket = settings.minio_bucket_name or 'images'
        safe_filename = get_safe_filename(filename)

        # 统一放在upload文件夹下
        object_name = f"upload/{safe_filename}"

        # 确保bucket存在
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)

        # 生成预签名上传URL（有效期1小时）
        from datetime import timedelta
        presigned_url = minio_client.presigned_put_object(bucket, object_name, expires=timedelta(hours=1))
        upload_url = _rewrite_presigned_url_for_browser(request, presigned_url)

        # 生成文件访问URL
        file_url = _build_public_file_url(request, bucket, object_name)

        logger.info(f"生成MinIO预签名URL: {object_name}")
        logger.info(f"MinIO内部预签名URL: {presigned_url}")
        logger.info(f"MinIO对外上传URL: {upload_url}")
        logger.info(f"MinIO对外文件URL: {file_url}")

        return {
            "upload_url": upload_url,
            "file_url": file_url,
            "filename": safe_filename,
            "bucket": bucket,
            "object_name": object_name
        }
    except Exception as e:
        logger.error(f"生成MinIO预签名URL失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成上传URL失败: {str(e)}")


@router.get("/image-proxy")
async def image_proxy(url: str):
    """代理下载外部图片，解决跨域问题"""
    url = unquote(url)
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="无效的图片URL")
    try:
        async with _httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg")
        # 从 URL 提取文件名
        filename = url.split("?")[0].rstrip("/").split("/")[-1] or "image.jpg"
        return _StreamingResponse(
            iter([resp.content]),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片下载失败: {str(e)}")


@router.get("/conversation/{conversation_id}", response_model=List[FileInfo])
async def get_conversation_files(conversation_id: str):
    """
    获取指定对话的所有文件
    """
    try:
        db_manager = get_db_manager()
        files = await db_manager.get_files_by_conversation(conversation_id)

        return [
            FileInfo(
                file_id=file.id,
                original_filename=file.original_filename,
                file_url=file.file_url,
                file_size=file.file_size,
                file_type=file.file_type,
                file_extension=file.file_extension,
                category=file.category,
                uploaded_at=file.created_at
            )
            for file in files
        ]

    except Exception as e:
        logger.error(f"获取对话文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")


@router.get("/message/{message_id}", response_model=List[FileInfo])
async def get_message_files(message_id: int):
    """
    获取指定消息的所有文件
    """
    try:
        db_manager = get_db_manager()
        files = await db_manager.get_files_by_message(message_id)

        return [
            FileInfo(
                file_id=file.id,
                original_filename=file.original_filename,
                file_url=file.file_url,
                file_size=file.file_size,
                file_type=file.file_type,
                file_extension=file.file_extension,
                category=file.category,
                uploaded_at=file.created_at
            )
            for file in files
        ]

    except Exception as e:
        logger.error(f"获取消息文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(file_id: int):
    """
    删除文件（软删除）
    """
    try:
        db_manager = get_db_manager()
        deleted = await db_manager.delete_uploaded_file(file_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="文件不存在")

        return {
            "status": "success",
            "file_id": file_id,
            "message": "文件已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
