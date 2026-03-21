"""Error classification utilities for retry mechanism."""

from enum import Enum
from typing import Optional


class ErrorType(Enum):
    """Error classification types."""
    RETRYABLE = "retryable"  # 可重试错误（临时性）
    NON_RETRYABLE = "non_retryable"  # 不可重试错误（永久性）
    UNKNOWN = "unknown"  # 未知错误


# HTTP状态码分类
RETRYABLE_STATUS_CODES = {
    429,  # Too Many Requests (限流)
    502,  # Bad Gateway (网关错误)
    503,  # Service Unavailable (服务不可用)
    504,  # Gateway Timeout (网关超时)
}

NON_RETRYABLE_STATUS_CODES = {
    400,  # Bad Request (请求参数错误)
    401,  # Unauthorized (认证失败)
    403,  # Forbidden (权限不足)
    404,  # Not Found (资源不存在)
    422,  # Unprocessable Entity (参数验证失败)
}


def classify_error(
    error: Exception,
    http_status: Optional[int] = None
) -> ErrorType:
    """
    分类错误类型

    可重试错误:
    - 429: 请求过于频繁（限流）
    - 502, 503, 504: 网关错误/服务不可用/超时
    - 超时错误 (TimeoutError, asyncio.TimeoutError)
    - 网络连接错误 (ConnectionError, OSError)

    不可重试错误:
    - 400: 请求参数错误
    - 401: 认证失败
    - 422: 参数验证失败
    - 内容违规等业务错误 (ValueError with specific messages)
    - 权限错误 (PermissionError)

    Args:
        error: 异常对象
        http_status: HTTP状态码（如果有）

    Returns:
        ErrorType: 错误类型
    """
    # 首先检查HTTP状态码
    if http_status is not None:
        if http_status in RETRYABLE_STATUS_CODES:
            return ErrorType.RETRYABLE
        if http_status in NON_RETRYABLE_STATUS_CODES:
            return ErrorType.NON_RETRYABLE

    # 根据异常类型判断
    error_type_name = type(error).__name__

    # 可重试的异常类型
    if error_type_name in ('TimeoutError', 'asyncio.TimeoutError'):
        return ErrorType.RETRYABLE
    if error_type_name in ('ConnectionError', 'ConnectionRefusedError',
                           'ConnectionResetError', 'OSError'):
        return ErrorType.RETRYABLE

    # 检查是否为网络相关错误
    error_msg = str(error).lower()
    retryable_keywords = [
        'timeout', 'timed out',
        'connection', 'network', 'network unreachable',
        'temporary', 'temporarily',
        'rate limit', 'too many requests',
        'service unavailable', 'bad gateway',
    ]

    for keyword in retryable_keywords:
        if keyword in error_msg:
            return ErrorType.RETRYABLE

    # 不可重试的异常类型
    if error_type_name in ('ValueError', 'PermissionError', 'ValidationError'):
        # 检查错误消息，确认是否为业务逻辑错误
        non_retryable_keywords = [
            'invalid', 'parameter', 'authentication', 'unauthorized',
            'forbidden', 'not found', 'violate', 'blocked content',
            'platform rules', 'invalid_parameter',
        ]

        for keyword in non_retryable_keywords:
            if keyword in error_msg:
                return ErrorType.NON_RETRYABLE

    # 默认为未知错误，建议不重试（保守策略）
    return ErrorType.UNKNOWN


def is_retryable_error(error: Exception, http_status: Optional[int] = None) -> bool:
    """
    判断错误是否可重试

    Args:
        error: 异常对象
        http_status: HTTP状态码（如果有）

    Returns:
        bool: 是否可重试
    """
    error_type = classify_error(error, http_status)
    return error_type == ErrorType.RETRYABLE
