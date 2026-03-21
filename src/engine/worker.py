"""工作协程"""

import asyncio
from typing import Optional, List
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
from ..utils.error_classifier import classify_error, ErrorType


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
        """处理任务（带重试机制）"""
        # 更新任务状态为运行中
        task.update_status(TaskStatus.RUNNING)
        task.progress = 0.0

        # 获取重试配置
        max_retries = getattr(settings, 'max_generation_retries', 2)
        base_delay = getattr(settings, 'retry_base_delay', 1.0)
        max_delay = getattr(settings, 'retry_max_delay', 10.0)
        max_attempts = max_retries + 1  # 总尝试次数 = 原始 + 重试

        last_error: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Worker {self.worker_id} 尝试 #{attempt}/{max_attempts} 处理任务 {task.task_id}")

                # 1. 参数提取（如果需要）- 只在第一次尝试时执行
                if attempt == 1 and not task.params.prompt:
                    task = await self._extract_prompt(task)
                    task.progress = 0.1

                # 2. 语义匹配增强参数 - 只在第一次尝试时执行
                if attempt == 1:
                    task = await self._enhance_params(task)
                    task.progress = 0.2

                # 3. 获取Provider并生成图片
                provider = get_provider(
                    task.params.provider or settings.default_image_provider,
                    api_key=task.params.api_key
                )

                # 生成图片（provider内部已有重试机制）
                images = await provider.generate(task.params)
                task.progress = 0.5

                # 4. 验证图片数据有效性
                if not self._validate_image_results(images):
                    raise ValueError("未获取到有效的图片数据")

                task.progress = 0.7

                # 5. 保存图片到存储
                results = await self._save_images(task, images)
                if not results:
                    raise ValueError("保存图片失败")

                task.result = results
                task.images = [{"url": img.url, "alt": f"生成的图像"} for img in results]
                task.progress = 0.9

                # 6. 处理成功：扣费并记录
                await self._handle_success(task, results)

                task.update_status(TaskStatus.COMPLETED)
                task.progress = 1.0

                # 7. 保存到数据库
                await self._save_to_database(task, results)

                if attempt > 1:
                    logger.info(f"Worker {self.worker_id} 任务 {task.task_id} 第 {attempt} 次尝试成功")
                else:
                    logger.info(f"Worker {self.worker_id} 完成任务 {task.task_id}")

                return task

            except Exception as e:
                last_error = e
                error_type = classify_error(e)

                # 判断是否应该重试
                if error_type == ErrorType.NON_RETRYABLE or attempt >= max_attempts:
                    # 不可重试错误或已达最大重试次数
                    if attempt == max_attempts:
                        logger.error(
                            f"任务 {task.task_id} 已达最大重试次数 ({max_attempts})，放弃重试"
                        )
                    else:
                        logger.error(
                            f"任务 {task.task_id} 不可重试错误 ({error_type.value})，立即失败: {str(e)[:200]}"
                        )
                    # 处理失败
                    await self._handle_failure(task, e, attempt)
                    return task

                # 可重试错误：等待后重试
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logger.warning(
                    f"任务 {task.task_id} 第 {attempt} 次尝试失败 ({error_type.value})，"
                    f"{delay}秒后重试: {str(e)[:200]}"
                )
                await asyncio.sleep(delay)

        # 理论上不会到达这里
        if last_error:
            await self._handle_failure(task, last_error, max_attempts)
        return task

    async def _extract_prompt(self, task: ImageTask) -> ImageTask:
        """提取提示词（如果需要）"""
        extractor = get_extractor(self.extractor_provider, api_key=task.params.api_key)
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
        return task

    async def _enhance_params(self, task: ImageTask) -> ImageTask:
        """语义匹配增强参数"""
        matcher = get_matcher(self.matcher_provider, api_key=task.params.api_key)
        user_input = task.metadata.get("user_input", task.params.prompt)
        task.params = await matcher.enhance_params(task.params, user_input)
        return task

    def _validate_image_results(self, images: List) -> bool:
        """
        验证图片结果有效性

        Returns:
            bool: 是否有有效的图片数据
        """
        if not images:
            return False

        # 检查是否至少有一个有效的图片数据
        for img in images:
            if isinstance(img, str) and img.startswith("data:image/"):
                return True
            if isinstance(img, bytes):
                return True
            if hasattr(img, 'url') and img.url:
                return self._is_valid_url(img.url)

        return False

    def _is_valid_url(self, url: str) -> bool:
        """检查URL格式是否有效"""
        if not url:
            return False
        return url.startswith(('http://', 'https://'))

    async def _save_images(self, task: ImageTask, images: List) -> List:
        """保存图片到存储"""
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

        return results

    async def _handle_success(self, task: ImageTask, results: List) -> None:
        """处理成功：扣费并记录"""
        logger.info(f"任务 {task.task_id} 生成成功: {len(results)}张图片")

        # 获取用户ID
        user_id = task.user_id
        if not user_id and task.user_request_id:
            try:
                db_manager = get_db_manager()
                user_request = await db_manager.get_user_request_by_id(task.user_request_id)
                if user_request:
                    user_id = user_request.user_id
            except Exception as e:
                logger.warning(f"无法从user_request获取user_id: {str(e)}")

        # 扣费（仅在成功后）
        if user_id:
            try:
                from ..services.account_service import get_account_service
                account_service = get_account_service()

                # 验证图片URL
                image_urls = [img.url for img in results if self._is_valid_url(img.url)]
                if not image_urls:
                    raise ValueError("没有有效的图片URL，不应扣费")

                await account_service.deduct_cost_on_success(
                    user_id=user_id,
                    model_name=task.params.model or "unknown",
                    provider=task.params.provider or "unknown",
                    request_id=task.task_id,
                    prompt=task.params.prompt,
                    image_count=len(image_urls),
                    image_urls=image_urls
                )
                logger.info(f"用户 {user_id} 扣费成功，任务 {task.task_id}")
            except Exception as billing_error:
                logger.error(f"扣费失败: {str(billing_error)}")
                # 扣费失败不影响任务完成状态

    async def _handle_failure(self, task: ImageTask, error: Exception, attempt: int) -> None:
        """处理失败：记录但不扣费"""
        logger.error(f"Worker {self.worker_id} 任务 {task.task_id} 第{attempt}次尝试失败: {str(error)}")

        task.update_status(TaskStatus.FAILED)
        task.error = f"尝试{attempt}次后失败: {str(error)}"
        task.progress = 0.0

        # 记录失败（不扣费）
        user_id = task.user_id
        if not user_id and task.user_request_id:
            try:
                db_manager = get_db_manager()
                user_request = await db_manager.get_user_request_by_id(task.user_request_id)
                if user_request:
                    user_id = user_request.user_id
            except Exception:
                pass

        if user_id:
            try:
                from ..services.account_service import get_account_service
                account_service = get_account_service()
                await account_service.record_generation_failure(
                    user_id=user_id,
                    model_name=task.params.model or "unknown",
                    provider=task.params.provider or "unknown",
                    request_id=task.task_id,
                    prompt=task.params.prompt,
                    error_reason=str(error)
                )
            except Exception as billing_error:
                logger.error(f"记录失败出错: {str(billing_error)}")

    async def _save_to_database(self, task: ImageTask, results: List) -> None:
        """保存到数据库"""
        if not task.user_request_id:
            return

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
                session_id = task.metadata.get("session_id")
                if session_id:
                    await db_manager.update_session_stats(session_id, image_increment=len(results))
                    await db_manager.save_images_to_conversation(session_id, image_urls, task.task_id)
                    logger.info(f"更新会话 {session_id} 的图片计数: {len(results)}")
            except Exception as session_error:
                logger.warning(f"更新会话统计和保存图片失败: {str(session_error)}")

            logger.info(f"任务 {task.task_id} 已保存到数据库")
        except Exception as e:
            logger.error(f"保存任务 {task.task_id} 到数据库失败: {str(e)}")

