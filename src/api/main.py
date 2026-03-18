"""FastAPI应用入口"""

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger
import sys

from ..config.settings import settings
from ..config.model_registry import get_model_registry
from ..engine import TaskManager
from ..database import get_db_manager
from .middleware import setup_cors, logging_middleware
from .routes import generate, batch, status, models, unified, chat, assistant, health, history, files, async_tasks


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    f"{settings.log_dir}/app.log",
    rotation=settings.log_rotation,
    retention=settings.log_retention,
    level=settings.log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动应用...")

    # 初始化数据库
    try:
        db_manager = get_db_manager()
        # 自动建表
        from ..database.base import Base
        from ..database import models  # noqa: F401 确保所有模型注册到 Base
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        app.state.db_manager = db_manager
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        # 数据库初始化失败不影响应用启动
        app.state.db_manager = None

    # 初始化异步任务数据库
    try:
        from ..database.async_task_manager import get_async_task_manager
        async_task_manager = get_async_task_manager()
        await async_task_manager.init_db()
        app.state.async_task_manager = async_task_manager
        logger.info("异步任务数据库初始化成功")

        # 启动异步任务处理器
        from ..engine.async_task_processor import AsyncTaskProcessor
        async_processor = AsyncTaskProcessor()
        await async_processor.start()
        app.state.async_processor = async_processor
        logger.info("异步任务处理器已启动")
    except Exception as e:
        logger.error(f"异步任务初始化失败: {str(e)}")
        app.state.async_task_manager = None
        app.state.async_processor = None

    # 初始化模型注册表（动态发现模型）
    try:
        model_registry = await get_model_registry()
        image_models = model_registry.list_image_models()
        logger.info(f"模型注册表初始化成功，发现 {len(image_models)} 个图像模型")
        app.state.model_registry = model_registry
    except Exception as e:
        logger.warning(f"模型注册表初始化失败: {str(e)}，将使用默认Provider")
        app.state.model_registry = None

    # 初始化任务管理器
    task_manager = TaskManager(
        extractor_provider=settings.default_llm_provider,
        matcher_provider=settings.default_embedding_provider,
    )
    await task_manager.start()
    app.state.task_manager = task_manager

    logger.info("应用启动完成")

    yield

    # 关闭时
    logger.info("关闭应用...")
    await task_manager.stop()

    # 停止异步任务处理器
    if hasattr(app.state, 'async_processor') and app.state.async_processor:
        await app.state.async_processor.stop()

    # 关闭数据库连接
    if app.state.db_manager:
        await app.state.db_manager.close()

    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="智能体生图应用 - 支持多Provider、并行批量生成",
    lifespan=lifespan
)

# 设置中间件
setup_cors(app)
app.middleware("http")(logging_middleware)

# 注册路由
app.include_router(generate.router)
app.include_router(batch.router)
app.include_router(status.router)
app.include_router(models.router)
app.include_router(unified.router)
app.include_router(chat.router)
app.include_router(assistant.router)  # 新增：统一AI助手接口
app.include_router(history.router)  # 新增：对话历史管理接口
app.include_router(files.router)  # 新增：文件管理接口
app.include_router(async_tasks.router)  # 新增：异步任务接口
app.include_router(health.router)  # 健康检查路由

# 静态文件服务（用于访问生成的图片）
# 仅在使用本地存储时挂载静态文件路由
if settings.storage_type == "local":
    import os
    storage_path = settings.storage_path
    if os.path.exists(storage_path):
        app.mount(settings.storage_url_prefix, StaticFiles(directory=storage_path), name="storage")
else:
    # MinIO存储模式下，图片通过MinIO服务直接访问
    logger.info(f"使用 {settings.storage_type} 存储，静态文件路由未启用")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


def run() -> None:
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()

