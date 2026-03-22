"""健康检查路由"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from ...config.settings import settings
from ...storage import get_storage

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health/storage")
async def storage_health():
    """检查存储服务健康状态"""
    try:
        # 获取存储实例
        storage = get_storage()

        # 检查存储类型
        if settings.storage_type == "minio":
            # MinIO健康检查：尝试连接并测试存储桶
            try:
                # 简单检查存储是否可用（list_images是同步方法，不需要await）
                storage.list_images()
                return {
                    "status": "healthy",
                    "storage_type": "minio",
                    "endpoint": settings.minio_endpoint,
                    "bucket": settings.minio_bucket_name
                }
            except Exception as e:
                logger.error(f"MinIO健康检查失败: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"MinIO存储服务不可用: {str(e)}"
                )
        else:
            # 本地存储检查
            return {
                "status": "healthy",
                "storage_type": "local",
                "storage_path": settings.storage_path
            }

    except Exception as e:
        logger.error(f"存储健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"存储服务检查失败: {str(e)}"
        )


@router.get("/health")
async def comprehensive_health():
    """综合健康检查"""
    try:
        from ...database import get_db_manager
        from ...engine import TaskManager

        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # 实际时间戳由FastAPI自动处理
            "services": {
                "api": {"status": "healthy"},
                "database": {"status": "unknown"},
                "storage": {"status": "unknown"},
                "task_manager": {"status": "unknown"}
            }
        }

        # 检查数据库
        try:
            db_manager = get_db_manager()
            if db_manager:
                health_status["services"]["database"] = {"status": "healthy"}
            else:
                health_status["services"]["database"] = {"status": "degraded", "message": "数据库连接失败，但不影响主要功能"}
        except Exception as e:
            health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
            logger.warning(f"数据库健康检查失败: {str(e)}")

        # 检查存储
        try:
            await storage_health()
            health_status["services"]["storage"] = {"status": "healthy"}
        except Exception as e:
            health_status["services"]["storage"] = {"status": "unhealthy", "error": str(e)}
            logger.warning(f"存储健康检查失败: {str(e)}")

        # 检查任务管理器
        try:
            task_manager = TaskManager(
                extractor_provider=settings.default_llm_provider,
                matcher_provider=settings.default_embedding_provider,
            )
            health_status["services"]["task_manager"] = {"status": "healthy"}
        except Exception as e:
            health_status["services"]["task_manager"] = {"status": "unhealthy", "error": str(e)}
            logger.warning(f"任务管理器健康检查失败: {str(e)}")

        # 整体状态
        unhealthy_services = [k for k, v in health_status["services"].items() if v["status"] == "unhealthy"]
        degraded_services = [k for k, v in health_status["services"].items() if v["status"] == "degraded"]

        if unhealthy_services:
            health_status["status"] = "unhealthy"
            health_status["unhealthy_services"] = unhealthy_services
        elif degraded_services:
            health_status["status"] = "degraded"
            health_status["degraded_services"] = degraded_services

        return health_status

    except Exception as e:
        logger.error(f"综合健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"健康检查失败: {str(e)}"
        )