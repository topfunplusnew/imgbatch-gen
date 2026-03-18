"""图片存储模块"""

from typing import Union
from .local_storage import LocalStorage
from .minio_storage import MinioStorage
from .metadata import MetadataManager
from ..config.settings import settings


def get_storage() -> Union[LocalStorage, MinioStorage]:
    """根据配置获取存储实例"""
    if settings.storage_type == "minio":
        return MinioStorage()
    else:
        return LocalStorage()
