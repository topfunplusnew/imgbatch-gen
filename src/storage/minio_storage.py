"""MinIO图片存储"""

import uuid
from typing import Optional
from datetime import datetime, timedelta
from PIL import Image
import io
import logging

from minio import Minio
from minio.error import S3Error

from ..config.settings import settings
from ..models.image import ImageResult, ImageParams

# 设置日志记录器
logger = logging.getLogger(__name__)


class MinioStorage:
    """MinIO对象存储"""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: Optional[bool] = None,
        url_prefix: Optional[str] = None
    ):
        """初始化MinIO存储"""
        self.endpoint = endpoint or settings.minio_endpoint
        self.access_key = access_key or settings.minio_access_key
        self.secret_key = secret_key or settings.minio_secret_key
        self.bucket_name = bucket_name or settings.minio_bucket_name
        self.secure = secure if secure is not None else settings.minio_secure
        prefix = url_prefix or settings.minio_url_prefix
        if not prefix:
            scheme = "https" if self.secure else "http"
            prefix = f"{scheme}://{self.endpoint}/{self.bucket_name}"
        self.url_prefix = prefix

        # 初始化MinIO客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

        # 确保bucket存在
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"创建新的MinIO bucket: {self.bucket_name}")
                self.client.make_bucket(self.bucket_name)
                logger.info(f"成功创建bucket: {self.bucket_name}")
            else:
                logger.info(f"使用现有bucket: {self.bucket_name}")
        except S3Error as e:
            error_msg = f"无法访问MinIO或创建bucket {self.bucket_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"初始化MinIO bucket时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _generate_object_name(self, task_id: str, image_format: str = "png") -> str:
        """生成唯一对象名称"""
        image_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 按日期组织目录结构
        date_path = datetime.now().strftime("%Y-%m-%d")
        return f"{date_path}/{task_id}/{timestamp}_{image_id}.{image_format}"

    def _make_thumbnail(self, image_data: bytes, max_size: int = 400) -> bytes:
        """生成压缩缩略图（JPEG，最长边不超过max_size）"""
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        return buf.getvalue()

    def save_image(
        self,
        image_data: bytes,
        task_id: str,
        params: ImageParams,
        image_format: str = "png"
    ) -> ImageResult:
        """保存图片到MinIO"""
        # 生成对象名称
        object_name = self._generate_object_name(task_id, image_format)
        content_type = f"image/{image_format}"

        logger.info(f"准备保存图片到MinIO: bucket={self.bucket_name}, object={object_name}, size={len(image_data)}")

        try:
            # 获取图片信息
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            file_size = len(image_data)

            # 上传到MinIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(image_data),
                file_size,
                content_type=content_type
            )

            logger.info(f"成功上传图片到MinIO: {object_name}, 尺寸: {width}x{height}")

            # 生成缩略图并上传
            thumbnail_url = None
            try:
                thumb_data = self._make_thumbnail(image_data)
                thumb_object_name = object_name.rsplit(".", 1)[0] + "_thumb.jpg"
                self.client.put_object(
                    self.bucket_name,
                    thumb_object_name,
                    io.BytesIO(thumb_data),
                    len(thumb_data),
                    content_type="image/jpeg"
                )
                thumbnail_url = f"{self.url_prefix.rstrip('/')}/{thumb_object_name.lstrip('/')}"
                logger.info(f"成功上传缩略图: {thumb_object_name}")
            except Exception as e:
                logger.warning(f"生成缩略图失败，使用原图: {e}")

            # 生成URL
            url = f"{self.url_prefix.rstrip('/')}/{object_name.lstrip('/')}"

            # 创建结果对象
            image_id = object_name.replace(f".{image_format}", "")
            result = ImageResult(
                image_id=image_id,
                task_id=task_id,
                file_path=object_name,
                url=url,
                thumbnail_url=thumbnail_url,
                width=width,
                height=height,
                size=file_size,
                format=image_format,
                metadata={
                    "object_name": object_name,
                    "bucket_name": self.bucket_name,
                    "endpoint": self.endpoint,
                }
            )

            logger.info(f"图片保存完成，生成URL: {url}")
            return result

        except S3Error as e:
            error_msg = f"保存图片到MinIO失败: {str(e)}, bucket={self.bucket_name}, object={object_name}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"保存图片时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """根据image_id获取图片数据"""
        logger.debug(f"尝试从MinIO获取图片: {image_id}")

        try:
            # image_id就是object_name（去掉了扩展名）
            # 尝试不同的扩展名
            for ext in ["png", "jpg", "jpeg", "webp"]:
                object_name = f"{image_id}.{ext}"
                try:
                    logger.debug(f"尝试获取对象: {object_name}")
                    response = self.client.get_object(self.bucket_name, object_name)
                    data = response.read()
                    response.close()
                    response.release_conn()
                    logger.info(f"成功从MinIO获取图片: {object_name}, size: {len(data)}")
                    return data
                except S3Error as e:
                    logger.debug(f"对象不存在: {object_name}, 错误: {str(e)}")
                    continue
            logger.warning(f"未找到图片: {image_id}")
            return None
        except S3Error as e:
            error_msg = f"从MinIO获取图片失败: {str(e)}, image_id={image_id}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"获取图片数据时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def delete_image(self, image_id: str) -> bool:
        """删除图片"""
        logger.info(f"尝试删除MinIO图片: {image_id}")

        try:
            # 尝试删除不同扩展名的对象
            deleted_count = 0
            for ext in ["png", "jpg", "jpeg", "webp"]:
                object_name = f"{image_id}.{ext}"
                try:
                    self.client.remove_object(self.bucket_name, object_name)
                    deleted_count += 1
                    logger.info(f"成功删除MinIO对象: {object_name}")
                except S3Error:
                    continue

            if deleted_count > 0:
                logger.info(f"成功删除 {deleted_count} 个图片文件: {image_id}")
                return True
            else:
                logger.warning(f"未找到要删除的图片: {image_id}")
                return False
        except S3Error as e:
            error_msg = f"从MinIO删除图片失败: {str(e)}, image_id={image_id}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"删除图片时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_presigned_url(self, image_id: str, expires: int = 3600) -> Optional[str]:
        """生成预签名URL（临时访问链接）"""
        logger.info(f"为图片生成预签名URL: {image_id}, 过期时间: {expires}秒")

        try:
            # 尝试不同的扩展名
            for ext in ["png", "jpg", "jpeg", "webp"]:
                object_name = f"{image_id}.{ext}"
                try:
                    url = self.client.presigned_get_object(
                        self.bucket_name,
                        object_name,
                        expires=timedelta(seconds=expires)
                    )
                    logger.info(f"成功生成预签名URL: {object_name}")
                    return url
                except S3Error:
                    continue
            logger.warning(f"无法为图片生成预签名URL: {image_id}")
            return None
        except S3Error as e:
            error_msg = f"生成预签名URL失败: {str(e)}, image_id={image_id}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"生成预签名URL时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def list_images(self, prefix: str = "", recursive: bool = False) -> list:
        """列出图片"""
        logger.info(f"列出MinIO图片: prefix={prefix}, recursive={recursive}")

        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            image_list = [{"name": obj.object_name, "size": obj.size} for obj in objects]
            logger.info(f"找到 {len(image_list)} 个图片")
            return image_list
        except S3Error as e:
            error_msg = f"列出MinIO对象失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"列出图片时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
