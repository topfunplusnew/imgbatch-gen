"""CSV文件解析器"""

import csv
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseParser


class CSVParser(BaseParser):
    """CSV文件解析器"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析CSV文件"""
        return Path(file_path).suffix.lower() == ".csv"
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """解析CSV文件"""
        try:
            results = []
            
            with open(file_path, "r", encoding="utf-8-sig") as f:
                # 尝试检测编码
                try:
                    reader = csv.DictReader(f)
                except UnicodeDecodeError:
                    f.seek(0)
                    reader = csv.DictReader(f, encoding="gbk")
                
                headers = [h.lower().strip() for h in reader.fieldnames or []]
                
                # 查找prompt列
                prompt_key = None
                for key in headers:
                    if any(keyword in key for keyword in ["prompt", "描述", "文本", "内容", "text", "description"]):
                        prompt_key = key
                        break
                
                if not prompt_key and headers:
                    prompt_key = headers[0]
                
                # 读取数据行
                for row in reader:
                    data = {}
                    
                    # 提取prompt
                    if prompt_key and prompt_key in row and row[prompt_key]:
                        data["prompt"] = str(row[prompt_key]).strip()
                    
                    # 提取其他参数
                    for key, value in row.items():
                        if key.lower() == prompt_key:
                            continue
                        if value:
                            # 尝试转换为数字
                            try:
                                if "." in str(value):
                                    data[key.lower()] = float(value)
                                else:
                                    data[key.lower()] = int(value)
                            except ValueError:
                                data[key.lower()] = str(value).strip()
                    
                    if data.get("prompt"):
                        results.append(data)
            
            return results
            
        except Exception as e:
            raise ValueError(f"解析CSV文件失败: {str(e)}")


