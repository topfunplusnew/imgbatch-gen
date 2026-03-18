"""图片解析器 - 从图片中提取文本（OCR，可选）"""

import os
from typing import List, Dict, Any
from PIL import Image

from .base import BaseParser


class ImageParser(BaseParser):
    """图片解析器 - 使用OCR提取文本（需要安装pytesseract）"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析该文件"""
        suffix = os.path.splitext(file_path)[1].lower()
        return suffix in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析图片并提取文本
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            包含提取文本的数据列表
        """
        try:
            # 尝试导入OCR库
            try:
                import pytesseract
                has_ocr = True
            except ImportError:
                has_ocr = False
            
            if not has_ocr:
                # 如果没有OCR库，返回图片路径作为提示词
                return [{
                    "prompt": f"根据图片生成图像: {os.path.basename(file_path)}",
                    "source": "image_file",
                    "file_path": file_path
                }]
            
            # 打开图片
            image = Image.open(file_path)
            
            # 使用OCR提取文本
            try:
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            except Exception:
                # OCR失败，使用默认提示词
                text = f"根据图片生成图像: {os.path.basename(file_path)}"
            
            # 清理文本
            text = text.strip()
            
            if not text:
                return [{
                    "prompt": f"根据图片生成图像: {os.path.basename(file_path)}",
                    "source": "image_file",
                    "file_path": file_path
                }]
            
            # 按行分割，每行作为一个prompt
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            result = []
            for line in lines:
                result.append({
                    "prompt": line,
                    "source": "image_ocr",
                    "file_path": file_path
                })
            
            return result
            
        except Exception as e:
            # 如果解析失败，返回默认提示词
            return [{
                "prompt": f"根据图片生成图像: {os.path.basename(file_path)}",
                "source": "image_file",
                "file_path": file_path
            }]

