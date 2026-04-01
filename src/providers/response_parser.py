"""响应解析工具类（统一处理各种响应格式）"""

from typing import List, Dict, Any, Optional


class ResponseParser:
    """响应解析工具类"""
    
    @staticmethod
    def extract_urls(response: Dict[str, Any] | List) -> List[str]:
        """
        从响应中提取图片URL（支持多种格式）

        支持的格式：
        1. { "data": { "images": [{ "url": "..." }] } }
        2. { "images": [{ "url": "..." }] }
        3. { "data": [{ "url": "..." }] }
        4. [{ "url": "..." }]
        5. ["url1", "url2"]
        6. { "imageUrl": "..." }
        7. { "url": "..." }
        8. Chat completions格式: { "choices": [{ "message": { "content": "![image](data:image/png;base64,...)" }] }
        """
        urls = []

        # 如果是列表，直接处理
        if isinstance(response, list):
            for item in response:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("imageUrl")
                    if url:
                        urls.append(url)
                elif isinstance(item, str):
                    urls.append(item)
            return urls

        # 如果是字典
        if not isinstance(response, dict):
            return urls

        # 格式8: Chat completions格式（优先检查）
        if "choices" in response:
            choices = response["choices"]
            if isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and "message" in first_choice:
                    message = first_choice["message"]
                    content = message.get("content", "")
                    # 提取markdown格式的图片
                    import re
                    # 匹配 ![...](url) 格式，支持 http/https/data URI
                    matches = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', content)
                    if matches:
                        urls.extend(matches)

        # 格式1: { "data": { "images": [...] } }
        if not urls and "data" in response:
            data = response["data"]
            if isinstance(data, dict):
                images = data.get("images", [])
                if images:
                    urls.extend(ResponseParser._extract_from_list(images))
            elif isinstance(data, list):
                urls.extend(ResponseParser._extract_from_list(data))

        # 格式2: { "images": [...] }
        if not urls and "images" in response:
            images = response["images"]
            urls.extend(ResponseParser._extract_from_list(images))

        # 格式3: 单个URL字段
        if not urls:
            url = response.get("url") or response.get("imageUrl") or response.get("image_url")
            if url:
                urls.append(url)

        # 格式4: output字段（可能是字符串或列表）
        if not urls and "output" in response:
            output = response["output"]
            if isinstance(output, str):
                urls.append(output)
            elif isinstance(output, list):
                urls.extend([item for item in output if isinstance(item, str)])

        # 格式5: OutputFiles (Tencent VOD格式)
        if not urls and "OutputFiles" in response:
            output_files = response["OutputFiles"]
            if isinstance(output_files, list) and len(output_files) > 0:
                file_info = output_files[0]
                url = file_info.get("Url") or file_info.get("FileId")
                if url:
                    urls.append(url)

        return urls
    
    @staticmethod
    def _extract_from_list(items: List) -> List[str]:
        """从列表中提取URL"""
        urls = []
        for item in items:
            if isinstance(item, dict):
                url = item.get("url") or item.get("imageUrl") or item.get("image_url")
                if url:
                    urls.append(url)
                elif item.get("b64_json"):
                    # gpt-image-1 返回 base64，转为 data URI
                    urls.append(f"data:image/png;base64,{item['b64_json']}")
            elif isinstance(item, str):
                urls.append(item)
        return urls
    
    @staticmethod
    def extract_task_id(response: Dict[str, Any], keys: List[str] = None) -> Optional[str]:
        """
        从响应中提取任务ID
        
        Args:
            response: API响应
            keys: 可能的任务ID字段名列表，默认: ["result", "id", "task_id", "request_id", "TaskId"]
        """
        if keys is None:
            keys = ["result", "id", "task_id", "request_id", "TaskId"]
        
        for key in keys:
            value = response.get(key)
            if value:
                return str(value)
        
        return None


