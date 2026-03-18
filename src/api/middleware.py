"""中间件"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from loguru import logger
import time


def setup_cors(app):
    """设置CORS中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
            "http://121.41.81.114:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def logging_middleware(request: Request, call_next):
    """日志中间件"""
    start_time = time.time()
    
    # 记录请求
    logger.info(f"{request.method} {request.url.path}")
    
    # 处理请求
    response = await call_next(request)
    
    # 记录响应
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


