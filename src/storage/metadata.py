"""元数据管理"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime

from ..models.image import ImageResult, ImageParams
from ..config.settings import settings


class MetadataManager:
    """元数据管理器"""

    def __init__(self, storage_type: str = "local"):
        """
        初始化元数据管理器

        Args:
            storage_type: 存储类型 ("local" 或 "minio")
        """
        self.storage_type = storage_type

        if storage_type == "minio":
            # 使用MinIO存储元数据
            from .minio_storage import MinioStorage
            self.minio_client = MinioStorage()
            self.metadata_prefix = "metadata"
        else:
            # 使用本地文件系统存储元数据
            from pathlib import Path
            self.storage_path = Path(settings.storage_path)
            self.metadata_dir = self.storage_path / "metadata"
            self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_json_value(self, value: Any) -> Any:
        """移除不可 JSON 序列化的运行时字段。"""
        if isinstance(value, (bytes, bytearray)):
            return None
        if isinstance(value, dict):
            sanitized: Dict[str, Any] = {}
            for key, item in value.items():
                cleaned = self._sanitize_json_value(item)
                if cleaned is not None:
                    sanitized[key] = cleaned
            return sanitized
        if isinstance(value, list):
            sanitized_list = []
            for item in value:
                cleaned = self._sanitize_json_value(item)
                if cleaned is not None:
                    sanitized_list.append(cleaned)
            return sanitized_list
        if isinstance(value, tuple):
            sanitized_tuple = []
            for item in value:
                cleaned = self._sanitize_json_value(item)
                if cleaned is not None:
                    sanitized_tuple.append(cleaned)
            return sanitized_tuple
        return value
    
    def save_metadata(self, image_result: ImageResult, params: ImageParams):
        """保存图片元数据"""
        sanitized_extra_params = self._sanitize_json_value(params.extra_params)
        if isinstance(params.extra_params, dict) and "image" in params.extra_params:
            sanitized_extra_params = dict(sanitized_extra_params or {})
            sanitized_extra_params["has_reference_image"] = True

        metadata = {
            "image_id": image_result.image_id,
            "task_id": image_result.task_id,
            "file_path": str(image_result.file_path),
            "url": image_result.url,
            "width": image_result.width,
            "height": image_result.height,
            "size": image_result.size,
            "format": image_result.format,
            "created_at": image_result.created_at.isoformat(),
            "params": {
                "prompt": params.prompt,
                "width": params.width,
                "height": params.height,
                "style": params.style,
                "quality": params.quality,
                "n": params.n,
                "provider": params.provider,
                "extra_params": sanitized_extra_params,
            },
            "metadata": image_result.metadata,
        }

        if self.storage_type == "minio":
            # 使用MinIO存储元数据
            import io
            from minio.error import S3Error

            # 按日期组织元数据目录结构，与图片保持一致
            date_path = datetime.now().strftime("%Y-%m-%d")
            object_name = f"{self.metadata_prefix}/{date_path}/{image_result.image_id}.json"
            metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
            metadata_bytes = metadata_json.encode("utf-8")

            try:
                self.minio_client.client.put_object(
                    self.minio_client.bucket_name,
                    object_name,
                    io.BytesIO(metadata_bytes),
                    len(metadata_bytes),
                    content_type="application/json"
                )
                print(f"元数据已保存到MinIO: {object_name}")
            except S3Error as e:
                raise Exception(f"保存元数据到MinIO失败: {str(e)}")
        else:
            # 使用本地文件系统存储元数据
            metadata_file = self.metadata_dir / f"{image_result.image_id}.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def load_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        """加载图片元数据"""
        if self.storage_type == "minio":
            # 从MinIO加载元数据
            import io
            from minio.error import S3Error

            # 尝试在不同日期目录中查找
            date_path = datetime.now().strftime("%Y-%m-%d")

            # 先尝试今天的日期目录
            object_name = f"{self.metadata_prefix}/{date_path}/{image_id}.json"
            try:
                response = self.minio_client.client.get_object(
                    self.minio_client.bucket_name,
                    object_name
                )
                metadata_data = response.read()
                response.close()
                response.release_conn()
                return json.loads(metadata_data)
            except S3Error:
                # 如果今天没有找到，尝试其他日期（这里简化处理，实际应用可能需要更好的查找逻辑）
                return None
        else:
            # 从本地文件系统加载元数据
            metadata_file = self.metadata_dir / f"{image_id}.json"
            if not metadata_file.exists():
                return None

            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
    
    def list_metadata(self, task_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """列出元数据（可选按task_id过滤）"""
        metadata_list = []

        if self.storage_type == "minio":
            # 从MinIO列出元数据
            from minio.error import S3Error

            try:
                # 列出所有元数据对象
                objects = self.minio_client.client.list_objects(
                    self.minio_client.bucket_name,
                    prefix=self.metadata_prefix,
                    recursive=True
                )

                for obj in objects:
                    if not obj.object_name.endswith(".json"):
                        continue

                    try:
                        response = self.minio_client.client.get_object(
                            self.minio_client.bucket_name,
                            obj.object_name
                        )
                        metadata_data = response.read()
                        response.close()
                        response.release_conn()

                        metadata = json.loads(metadata_data)
                        if task_id is None or metadata.get("task_id") == task_id:
                            metadata_list.append(metadata)
                    except Exception:
                        continue

            except S3Error as e:
                raise Exception(f"从MinIO列出元数据失败: {str(e)}")
        else:
            # 从本地文件系统列出元数据
            for metadata_file in self.metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        if task_id is None or metadata.get("task_id") == task_id:
                            metadata_list.append(metadata)
                except Exception:
                    continue

        return sorted(metadata_list, key=lambda x: x.get("created_at", ""), reverse=True)

