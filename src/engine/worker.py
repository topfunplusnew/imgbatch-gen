"""工作协程"""

import asyncio
from typing import Optional
from datetime import datetime
from loguru import logger

from ..models.task import ImageTask, TaskStatus
from ..models.image import ImageParams
from ..providers import get_provider
from ..storage import MetadataManager
from typing import Union
from ..extractor import get_extractor
from ..matcher import get_matcher
from ..config.settings import settings
from ..database import get_db_manager


class Worker:
    """工作协程"""
    
    def __init__(
        self,
        worker_id: int,
        storage: Union[object, 'LocalStorage', 'MinioStorage'],
        metadata_manager: MetadataManager,
        extractor_provider: Optional[str] = None,
        matcher_provider: Optional[str] = None,
    ):
        """初始化工作协程"""
        self.worker_id = worker_id
        self.storage = storage
        self.metadata_manager = metadata_manager
        self.extractor_provider = extractor_provider
        self.matcher_provider = matcher_provider
        self.running = False
    
    async def process_task(self, task: ImageTask) -> ImageTask:
        """处理任务"""
        try:
            # 更新任务状态
            task.update_status(TaskStatus.RUNNING)
            task.progress = 0.1
            
            # 1. 参数提取（如果需要）
            if not task.params.prompt:
                extractor = get_extractor(self.extractor_provider, api_key=task.params.api_key)
                # 假设有原始输入在metadata中
                user_input = task.metadata.get("user_input", "")
                if user_input:
                    # 保存现有参数（如宽高等）
                    original_width = task.params.width
                    original_height = task.params.height
                    original_quality = task.params.quality
                    original_n = task.params.n

                    extracted_params = await extractor.extract(user_input)

                    # 如果LLM提取没有指定宽高，使用原有值
                    if extracted_params.width == 1024 and extracted_params.height == 1024:
                        extracted_params.width = original_width
                        extracted_params.height = original_height

                    # 保留其他原有参数
                    if extracted_params.quality == "standard" and original_quality != "standard":
                        extracted_params.quality = original_quality
                    if extracted_params.n == 1 and original_n != 1:
                        extracted_params.n = original_n

                    task.params = extracted_params
                    task.progress = 0.3
            
            # 2. 语义匹配增强参数
            matcher = get_matcher(self.matcher_provider, api_key=task.params.api_key)
            user_input = task.metadata.get("user_input", task.params.prompt)
            task.params = await matcher.enhance_params(task.params, user_input)
            task.progress = 0.5
            
            # 3. 获取Provider并生成图片
            provider = get_provider(task.params.provider or settings.default_image_provider, api_key=task.params.api_key)
            images = await provider.generate(task.params)
            task.progress = 0.7
            
            # 4. 保存图片
            results = []
            storage_type = self.storage.__class__.__name__
            logger.info(f"使用 {storage_type} 存储图片")

            for image_data in images:
                # data:image/ base64 字符串解码为 bytes
                if isinstance(image_data, str) and image_data.startswith("data:image/"):
                    import base64
                    comma = image_data.find(",")
                    image_data = base64.b64decode(image_data[comma + 1:] if comma >= 0 else image_data)
                elif isinstance(image_data, bytes):
                    # 尝试解码为 data URI，失败则直接当 bytes 用
                    try:
                        s = image_data.decode("utf-8")
                        if s.startswith("data:image/"):
                            import base64
                            comma = s.find(",")
                            image_data = base64.b64decode(s[comma + 1:] if comma >= 0 else s)
                    except (UnicodeDecodeError, ValueError):
                        pass  # 已经是原始图片 bytes，直接使用

                result = self.storage.save_image(
                    image_data=image_data,
                    task_id=task.task_id,
                    params=task.params,
                    image_format="png"
                )
                results.append(result)

                # 保存元数据
                self.metadata_manager.save_metadata(result, task.params)
            
            task.result = results
            task.images = [{"url": img.url, "alt": f"生成的图像"} for img in results]
            task.update_status(TaskStatus.COMPLETED)
            task.progress = 1.0

            # 5. 保存到数据库
            if task.user_request_id:
                try:
                    db_manager = get_db_manager()

                    # 准备图片URL列表
                    image_urls = [img.url for img in results]

                    # 创建图片生成记录
                    image_record = await db_manager.create_image_generation_record(
                        user_request_id=task.user_request_id,
                        provider=task.params.provider,
                        model=task.params.model or "",
                        prompt=task.params.prompt,
                        negative_prompt=task.params.negative_prompt,
                        width=task.params.width,
                        height=task.params.height,
                        n=task.params.n,
                        style=task.params.style,
                        quality=task.params.quality,
                        extra_params=task.params.extra_params or {},
                        status="completed",
                        image_urls=image_urls,
                        image_paths=[img.file_path for img in results],
                        processing_time=(datetime.now() - task.started_at).total_seconds() if task.started_at else 0,
                        call_mode=task.metadata.get("call_mode", "serial")
                    )

                    # 尝试获取会话ID并更新会话的图片计数
                    try:
                        # 从用户请求的元数据中获取会话ID
                        session_id = task.metadata.get("session_id")
                        if session_id:
                            # 更新会话的图片计数
                            await db_manager.update_session_stats(session_id, image_increment=len(results))

                            # 保存图片到对话
                            image_urls = [img.url for img in results]
                            await db_manager.save_images_to_conversation(session_id, image_urls, task.task_id)

                            logger.info(f"更新会话 {session_id} 的图片计数: {len(results)}")
                    except Exception as session_error:
                        logger.warning(f"更新会话统计和保存图片失败: {str(session_error)}")

                    logger.info(f"任务 {task.task_id} 已保存到数据库")
                except Exception as e:
                    logger.error(f"保存任务 {task.task_id} 到数据库失败: {str(e)}")

            logger.info(f"Worker {self.worker_id} 完成任务 {task.task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} 处理任务 {task.task_id} 失败: {str(e)}")
            task.update_status(TaskStatus.FAILED)
            task.error = str(e)
            task.progress = 0.0
            return task

