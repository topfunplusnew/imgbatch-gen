"""Word文档解析器"""

import os
from typing import List, Dict, Any
from docx import Document

from .base import BaseParser


class WordParser(BaseParser):
    """Word文档解析器"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析该文件"""
        suffix = os.path.splitext(file_path)[1].lower()
        return suffix in [".docx", ".doc"]
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析Word文档并提取文本
        
        Args:
            file_path: Word文档路径
            
        Returns:
            包含提取文本的数据列表
        """
        result = []
        
        try:
            # 打开Word文档
            doc = Document(file_path)
            
            # 提取所有段落文本
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
            
            if not paragraphs:
                return []
            
            # 每个段落作为一个prompt
            for para in paragraphs:
                result.append({
                    "prompt": para,
                    "source": "word",
                    "file_path": file_path
                })
                
        except Exception as e:
            # 如果解析失败，返回空列表
            return []
        
        return result


