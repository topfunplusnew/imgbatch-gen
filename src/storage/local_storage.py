"""本地图片存储"""

import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime
from PIL import Image
import io

from ..config.settings import settings
from ..models.image import ImageResult, ImageParams


class LocalStorage:
    """本地文件系统存储"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化本地存储"""
        self.storage_path = Path(storage_path or settings.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 按日期组织目录
        self._ensure_date_directory()
    
    def _ensure_date_directory(self):
        """确保日期目录存在"""
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.storage_path / today
        date_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_storage_path(self, task_id: Optional[str] = None) -> Path:
        """获取存储路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.storage_path / today
        
        if task_id:
            task_dir = date_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            return task_dir
        
        return date_dir
    
    def _generate_filename(self, image_format: str = "png") -> str:
        """生成唯一文件名"""
        image_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{image_id}.{image_format}"
    
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
        """保存图片"""
        # 获取存储路径
        storage_dir = self._get_storage_path(task_id)
        filename = self._generate_filename(image_format)
        file_path = storage_dir / filename
        
        # 保存图片
        with open(file_path, "wb") as f:
            f.write(image_data)

        # 获取图片信息
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        file_size = file_path.stat().st_size

        # 生成缩略图
        thumbnail_url = None
        try:
            thumb_data = self._make_thumbnail(image_data)
            thumb_path = storage_dir / (filename.rsplit(".", 1)[0] + "_thumb.jpg")
            with open(thumb_path, "wb") as f:
                f.write(thumb_data)
            thumb_relative = thumb_path.relative_to(self.storage_path)
            thumbnail_url = f"{settings.storage_url_prefix}/{thumb_relative.as_posix()}"
        except Exception as e:
            from loguru import logger
            logger.warning(f"生成缩略图失败，使用原图: {e}")

        # 生成URL（相对路径）
        relative_path = file_path.relative_to(self.storage_path)
        url = f"{settings.storage_url_prefix}/{relative_path.as_posix()}"

        # 创建结果对象
        image_id = filename.replace(f".{image_format}", "")
        result = ImageResult(
            image_id=image_id,
            task_id=task_id,
            file_path=str(file_path),
            url=url,
            thumbnail_url=thumbnail_url,
            width=width,
            height=height,
            size=file_size,
            format=image_format,
            metadata={
                "filename": filename,
                "storage_path": str(self.storage_path),
            }
        )
        
        return result
    
    def get_image_path(self, image_id: str) -> Optional[Path]:
        """根据image_id获取图片路径"""
        # 在metadata中查找
        from .metadata import MetadataManager
        metadata_manager = MetadataManager(str(self.storage_path))
        metadata = metadata_manager.load_metadata(image_id)
        
        if metadata and "file_path" in metadata:
            path = Path(metadata["file_path"])
            if path.exists():
                return path
        
        # 如果metadata中找不到，尝试在所有日期目录中搜索
        for date_dir in self.storage_path.iterdir():
            if not date_dir.is_dir():
                continue
            for file_path in date_dir.rglob(f"*{image_id}*"):
                if file_path.is_file():
                    return file_path
        
        return None
    
    def delete_image(self, image_id: str) -> bool:
        """删除图片"""
        image_path = self.get_image_path(image_id)
        if image_path and image_path.exists():
            image_path.unlink()
            
            # 删除元数据
            from .metadata import MetadataManager
            metadata_manager = MetadataManager(str(self.storage_path))
            metadata_file = metadata_manager.metadata_dir / f"{image_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            return True
        return False


