"""Excel文件解析器"""

import openpyxl
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseParser


class ExcelParser(BaseParser):
    """Excel文件解析器"""
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析Excel文件"""
        suffix = Path(file_path).suffix.lower()
        return suffix in (".xlsx", ".xls")
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """解析Excel文件"""
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active
            results = []
            
            # 读取表头
            headers = []
            header_row = sheet[1]
            for cell in header_row:
                headers.append(cell.value.lower() if cell.value else "")
            
            # 查找prompt列（支持多种可能的列名）
            prompt_col_idx = None
            for idx, header in enumerate(headers):
                if any(keyword in header for keyword in ["prompt", "描述", "文本", "内容", "text", "description"]):
                    prompt_col_idx = idx
                    break
            
            if prompt_col_idx is None and len(headers) > 0:
                # 如果没有找到prompt列，使用第一列
                prompt_col_idx = 0
            
            # 读取数据行
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=False), start=2):
                if not any(cell.value for cell in row):
                    continue
                
                data = {}
                
                # 提取prompt
                if prompt_col_idx is not None and prompt_col_idx < len(row):
                    prompt_cell = row[prompt_col_idx]
                    if prompt_cell.value:
                        data["prompt"] = str(prompt_cell.value).strip()
                
                # 提取其他参数
                for idx, header in enumerate(headers):
                    if idx == prompt_col_idx:
                        continue
                    if idx < len(row) and row[idx].value:
                        # 尝试转换为数字
                        value = row[idx].value
                        if isinstance(value, (int, float)):
                            data[header] = value
                        else:
                            data[header] = str(value).strip()
                
                if data.get("prompt"):
                    results.append(data)
            
            workbook.close()
            return results
            
        except Exception as e:
            raise ValueError(f"解析Excel文件失败: {str(e)}")


