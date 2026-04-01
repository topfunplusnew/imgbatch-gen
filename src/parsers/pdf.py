"""PDF解析器"""

import os
from typing import List, Dict, Any
import pdfplumber

from .base import BaseParser


class PDFParser(BaseParser):
    """PDF解析器"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析该文件"""
        suffix = os.path.splitext(file_path)[1].lower()
        return suffix == ".pdf"
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析PDF并提取文本
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            包含提取文本的数据列表
        """
        result = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                all_text = []
                
                # 提取所有页面的文本
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text.append(text.strip())
                
                # 合并所有文本
                full_text = "\n".join(all_text)
                
                if not full_text.strip():
                    return []
                
                # 按行分割，每行作为一个prompt
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                
                for line in lines:
                    result.append({
                        "prompt": line,
                        "source": "pdf",
                        "file_path": file_path
                    })
                
        except Exception as e:
            # 如果解析失败，返回空列表
            return []
        
        return result


