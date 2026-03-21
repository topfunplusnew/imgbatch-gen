"""Retry decorator with exponential backoff for async functions."""

import asyncio
from typing import Callable, TypeVar, Optional, List, Type, Any
from loguru import logger

from .error_classifier import classify_error, ErrorType


T = TypeVar('T')


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retryable_errors: Optional[List[Type[Exception]]] = None,
    operation_name: str = "operation",
) -> Any:
    """
    带指数退避的重试装饰器（异步）

    Args:
        func: 要重试的异步函数
        max_retries: 最大重试次数（默认2次，总共3次尝试）
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        retryable_errors: 可重试的异常类型列表（可选，默认使用error_classifier）
        operation_name: 操作名称（用于日志）

    Returns:
        函数执行结果

    Raises:
        Exception: 最后一次尝试的异常

    重试延迟：base_delay → base_delay*2 → base_delay*4 → ...（最大不超过max_delay）
    """
    max_attempts = max_retries + 1  # 总尝试次数 = 原始尝试 + 重试次数
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1:
                logger.info(f"{operation_name}: 尝试 #{attempt}/{max_attempts}")
            result = await func()
            # 成功：返回结果
            if attempt > 1:
                logger.info(f"{operation_name}: 第 {attempt} 次尝试成功")
            return result

        except Exception as e:
            last_error = e
            error_type = classify_error(e)

            # 判断是否应该重试
            should_retry = False
            if attempt < max_attempts:
                # 如果指定了可重试的异常类型，检查是否匹配
                if retryable_errors is not None:
                    should_retry = any(isinstance(e, error_cls) for error_cls in retryable_errors)
                else:
                    # 使用错误分类器
                    should_retry = (error_type == ErrorType.RETRYABLE)

            if not should_retry:
                # 不可重试错误或已达最大重试次数
                if attempt == max_attempts:
                    logger.error(
                        f"{operation_name}: 已达最大重试次数 ({max_attempts})，放弃重试"
                    )
                else:
                    logger.error(
                        f"{operation_name}: 不可重试错误 ({error_type.value})，立即失败: {str(e)}"
                    )
                raise

            # 可重试：等待后重试
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                f"{operation_name}: 第 {attempt} 次尝试失败 ({error_type.value})，"
                f"{delay}秒后重试: {str(e)[:200]}"
            )
            await asyncio.sleep(delay)

    # 理论上不会到达这里（应该在循环中返回或抛出异常）
    if last_error:
        raise last_error
    raise RuntimeError(f"{operation_name}: 重试逻辑异常")


class RetryableOperation:
    """
    可重试操作的上下文管理器（用于更复杂的重试场景）

    使用示例:
        async with RetryableOperation("生成图片", max_retries=2) as retry:
            result = await some_async_function()
            retry.set_result(result)
    """

    def __init__(
        self,
        operation_name: str,
        max_retries: int = 2,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
    ):
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_retries + 1
        self.attempt = 0
        self._result = None
        self._should_set_result = True

    async def __aenter__(self):
        self.attempt = 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False  # 正常退出，不抑制异常

        # 发生了异常，判断是否重试
        error = exc_val
        error_type = classify_error(error)

        if self.attempt >= self.max_attempts:
            # 已达最大重试次数
            logger.error(
                f"{self.operation_name}: 已达最大重试次数 ({self.max_attempts})，放弃重试"
            )
            return False  # 重新抛出异常

        if error_type != ErrorType.RETRYABLE:
            # 不可重试错误
            logger.error(
                f"{self.operation_name}: 不可重试错误 ({error_type.value})，立即失败: {str(error)[:200]}"
            )
            return False  # 重新抛出异常

        # 可重试：等待后重新进入
        delay = min(self.base_delay * (2 ** (self.attempt - 1)), self.max_delay)
        logger.warning(
            f"{self.operation_name}: 第 {self.attempt} 次尝试失败 ({error_type.value})，"
            f"{delay}秒后重试: {str(error)[:200]}"
        )
        await asyncio.sleep(delay)

        self.attempt += 1
        # 返回True表示抑制异常，继续重试
        return True

    def set_result(self, result: Any):
        """设置操作结果（用于在上下文管理器中传递结果）"""
        self._result = result

    def get_result(self) -> Any:
        """获取操作结果"""
        return self._result
