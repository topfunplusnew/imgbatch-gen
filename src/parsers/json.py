"""JSON文件解析器"""

import json
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseParser


class JSONParser(BaseParser):
    """JSON文件解析器"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析JSON文件"""
        return Path(file_path).suffix.lower() == ".json"
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """解析JSON文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            results = []
            
            # 如果数据是列表
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # 确保有prompt字段
                        if "prompt" not in item:
                            # 尝试查找可能的prompt字段
                            for key in ["text", "description", "描述", "内容", "文本"]:
                                if key in item:
                                    item["prompt"] = item.pop(key)
                                    break
                        if item.get("prompt"):
                            results.append(item)
            
            # 如果数据是字典
            elif isinstance(data, dict):
                # 检查是否有列表字段
                if "items" in data or "data" in data or "prompts" in data:
                    key = "items" if "items" in data else ("data" if "data" in data else "prompts")
                    items = data[key]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and item.get("prompt"):
                                results.append(item)
                else:
                    # 单个对象
                    if data.get("prompt"):
                        results.append(data)
            
            return results
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"解析JSON文件失败: {str(e)}")


