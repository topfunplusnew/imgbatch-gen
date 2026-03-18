"""TXT文件解析器"""

from typing import List, Dict, Any
from pathlib import Path

from .base import BaseParser


class TXTParser(BaseParser):
    """TXT文件解析器"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析TXT文件"""
        return Path(file_path).suffix.lower() == ".txt"
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """解析TXT文件"""
        try:
            # 尝试多种编码
            encodings = ["utf-8", "gbk", "gb2312", "utf-8-sig"]
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("无法读取文件，编码格式不支持")
            
            results = []
            
            # 按行分割，每行作为一个prompt
            lines = content.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    # 尝试解析为键值对格式（key: value）
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            key = parts[0].strip().lower()
                            value = parts[1].strip()
                            if key == "prompt" or key in ["描述", "文本", "内容", "text", "description"]:
                                results.append({"prompt": value})
                            else:
                                # 如果第一行不是prompt，创建一个包含该行的prompt
                                if not results:
                                    results.append({"prompt": line})
                                else:
                                    results[-1][key] = value
                        else:
                            results.append({"prompt": line})
                    else:
                        results.append({"prompt": line})
            
            return results
            
        except Exception as e:
            raise ValueError(f"解析TXT文件失败: {str(e)}")


