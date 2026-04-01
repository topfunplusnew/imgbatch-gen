"""文件解析器基础接口"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path


class BaseParser(ABC):
    """基础解析器接口"""
    
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析文件并提取数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的数据列表，每个元素包含prompt和可能的参数
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        检查是否可以解析该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否可以解析
        """
        pass
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """获取文件类型"""
        suffix = Path(file_path).suffix.lower()
        type_map = {
            ".xlsx": "excel",
            ".xls": "excel",
            ".csv": "csv",
            ".json": "json",
            ".txt": "txt",
            ".pdf": "pdf",
            ".docx": "word",
            ".doc": "word",
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".bmp": "image",
            ".gif": "image",
            ".tiff": "image",
            ".webp": "image",
        }
        return type_map.get(suffix, "unknown")

