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
from .routes import generate, batch, status, models, unified, chat, assistant, health, history, files, async_tasks, auth, account, payment, checkin, download, referral, admin, system_config, withdrawal, case_management, notifications, maintenance


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
    level=settings.log_level,
    encoding="utf-8"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动应用...")

    # 初始化数据库管理器（不自动建表）
    try:
        db_manager = get_db_manager()
        app.state.db_manager = db_manager
        logger.info("数据库管理器初始化成功")
    except Exception as e:
        logger.error(f"数据库管理器初始化失败: {str(e)}")
        app.state.db_manager = None

    # 初始化管理员账户（仅当不存在时）
    try:
        from ..database import User, Account
        from ..services.auth_service import AuthService

        async with db_manager.get_session() as session:
            from sqlalchemy import select

            # 检查是否已存在admin用户
            stmt = select(User).where(User.username == settings.default_admin_username)
            result = await session.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if not existing_admin:
                logger.info(f"创建初始管理员账户: {settings.default_admin_username}")

                # 创建管理员用户
                auth_service = AuthService()
                password_hash = await auth_service.hash_password(settings.default_admin_password)

                admin_user = User(
                    username=settings.default_admin_username,
                    password_hash=password_hash,
                    role="admin",
                    status="active",
                    force_password_change=True  # 强制首次登录后修改密码
                )
                session.add(admin_user)
                await session.flush()  # 获取user ID

                # 创建关联的账户记录
                admin_account = Account(
                    user_id=admin_user.id,
                    balance=0,
                    points=10000,  # 初始赠送积分
                    subscription_plan="free",
                    total_generated=0,
                    total_spent=0,
                    total_points_earned=10000,
                    free_quota_used=0,
                    subscription_quota_used=0,
                    gift_points=100,
                    consecutive_checkin_days=0,
                    total_invite_count=0
                )
                session.add(admin_account)
                await session.commit()

                logger.info(f"初始管理员账户创建成功: {settings.default_admin_username} (ID: {admin_user.id})")
                logger.warning("⚠️  请在生产环境中修改默认管理员密码！")
            else:
                logger.info(f"管理员账户已存在: {existing_admin.username}")
    except Exception as e:
        logger.error(f"初始化管理员账户失败: {str(e)}")
        # 不阻止应用启动，只记录错误

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

    # 初始化SSE管理器
    try:
        from ..utils.sse_manager import get_sse_manager
        sse_manager = get_sse_manager()
        await sse_manager.start()
        app.state.sse_manager = sse_manager
        logger.info("SSE管理器已启动")
    except Exception as e:
        logger.warning(f"SSE管理器启动失败: {str(e)}")
        app.state.sse_manager = None

    # 初始化后台调度器和数据保留清理服务
    try:
        from ..scheduler.background_scheduler import BackgroundScheduler
        from ..services.retention_cleanup import RetentionCleanupService

        scheduler = BackgroundScheduler()
        await scheduler.start()
        app.state.scheduler = scheduler

        # 创建清理服务实例，传入db_manager以复用连接池
        cleanup_service = RetentionCleanupService(db_manager=db_manager)
        app.state.cleanup_service = cleanup_service

        # 安排定期清理任务
        interval_seconds = settings.cleanup_interval_hours * 3600
        scheduler.schedule_periodic(
            name="retention_cleanup",
            interval_seconds=interval_seconds,
            coroutine_func=cleanup_service.cleanup_expired_records,
            retention_days=settings.retention_days,
            batch_size=settings.cleanup_batch_size,
            dry_run=settings.cleanup_dry_run
        )

        logger.info(
            f"数据保留清理服务已启动，"
            f"保留期: {settings.retention_days}天，"
            f"清理间隔: {settings.cleanup_interval_hours}小时"
        )

        # 如果配置了启动时清理
        if settings.cleanup_on_startup:
            logger.info("执行启动时清理...")
            from ..models.cleanup import CleanupReport
            report = await cleanup_service.cleanup_expired_records(
                retention_days=settings.retention_days,
                batch_size=settings.cleanup_batch_size,
                dry_run=settings.cleanup_dry_run
            )
            report.triggered_by = "startup"
            logger.info(
                f"启动时清理完成: "
                f"状态={report.status}, "
                f"删除记录={report.total_image_records_deleted}, "
                f"耗时={report.duration_seconds:.2f}秒"
            )

    except Exception as e:
        logger.error(f"数据保留清理服务初始化失败: {str(e)}")
        app.state.scheduler = None
        app.state.cleanup_service = None

    logger.info("应用启动完成")

    yield

    # 关闭时
    logger.info("关闭应用...")
    await task_manager.stop()

    # 停止异步任务处理器
    if hasattr(app.state, 'async_processor') and app.state.async_processor:
        await app.state.async_processor.stop()

    # 停止SSE管理器
    if hasattr(app.state, 'sse_manager') and app.state.sse_manager:
        await app.state.sse_manager.stop()

    # 停止后台调度器
    if hasattr(app.state, 'scheduler') and app.state.scheduler:
        await app.state.scheduler.stop()
        logger.info("后台调度器已停止")

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
app.include_router(auth.router)  # 认证路由
app.include_router(account.router)  # 账户路由
app.include_router(payment.router)  # 支付路由
app.include_router(checkin.router)  # 签到路由
app.include_router(download.router)  # 下载记录路由
app.include_router(referral.router)  # 邀请码路由
app.include_router(admin.router)  # 管理员路由
app.include_router(system_config.router)  # 系统配置路由
app.include_router(withdrawal.router)  # 提现路由
app.include_router(case_management.router)  # 案例管理路由（用户）
app.include_router(case_management.admin_router)  # 案例管理路由（管理员）
app.include_router(notifications.router)  # 通知系统路由（用户）
app.include_router(notifications.admin_router)  # 通知系统路由（管理员）
app.include_router(maintenance.router)  # 维护和清理路由
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

