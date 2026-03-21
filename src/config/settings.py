"""应用配置管理"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用主配置"""
    
    # 应用基础配置
    app_name: str = "智能体生图应用"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8888
    
    # 存储配置
    storage_type: str = "local"  # 存储类型: "local" 或 "minio"
    storage_path: str = "./storage"
    storage_url_prefix: str = "/storage"

    # MinIO配置
    minio_endpoint: str = "121.41.81.114:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "admin123"
    minio_bucket_name: str = "images"
    minio_secure: bool = False  # 是否使用HTTPS
    minio_url_prefix: Optional[str] = None  # MinIO文件访问URL前缀，从环境变量 MINIO_URL_PREFIX 读取
    public_base_url: Optional[str] = None  # 对外访问的应用基础地址，用于生成给前端的完整URL
    
    # 任务引擎配置
    max_concurrent_tasks: int = 20
    task_timeout: int = 300
    
    # 默认Provider
    default_image_provider: str = "openai"
    default_llm_provider: str = "relay"  # 使用中转站调用LLM
    default_embedding_provider: str = "relay"  # 使用中转站调用Embedding
    
    # 中转站配置（所有绘图模型统一使用）
    relay_base_url: str = "https://api.yiwuxueshe.cn"
    relay_api_key: Optional[str] = None  # 中转站API Key，从前端传入
    credential_encryption_key: Optional[str] = None
    credential_ttl_hours: int = 24
    
    # 模型配置API
    config_api_url: Optional[str] = None  # 模型配置接口URL，从.env文件读取
    config_cache_ttl_hours: int = 1  # 模型配置缓存时间（小时）

    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_image_model: str = "dall-e-3"

    # Assistant multimodal orchestration
    assistant_text_model: str = "gpt-4o-mini"
    assistant_planner_model: str = "gpt-4o-mini"
    assistant_ocr_model: str = "qwen3-vl-plus"
    assistant_attachment_text_limit: int = 12000
    assistant_pdf_ocr_max_pages: int = 6
    assistant_pdf_native_text_threshold: int = 120

    # LangChain / LangGraph document workflow
    langchain_pdf_prompt_model: str = "gpt-4o-mini"
    langchain_pdf_max_pages: int = 12
    langchain_pdf_page_char_limit: int = 5000
    

    
    # Stable Diffusion配置
    stable_diffusion_api_url: str = "http://localhost:7860"
    stable_diffusion_api_key: Optional[str] = None
    
    # 百度文心配置
    baidu_api_key: Optional[str] = None
    baidu_secret_key: Optional[str] = None
    baidu_image_model: str = "ernie-vilg-v2"
    
    # 阿里通义配置
    aliyun_api_key: Optional[str] = None
    aliyun_image_model: str = "wanx-v1"
    
    # 日志配置
    log_dir: str = "./logs"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    # 数据库配置（使用PostgreSQL + asyncpg驱动）
    # 格式: postgresql+asyncpg://user:password@host:port/database
    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/agent_db"
    database_echo: bool = False  # 是否输出SQL日志

    # PostgreSQL数据库配置（可选，用于构建连接字符串）
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "1234"
    postgres_database: str = "agent_db"

    # ==================== 重试机制配置 ====================

    # 图片生成重试配置
    max_generation_retries: int = 2  # 图片生成最大重试次数（默认2次，总共3次尝试）
    retry_base_delay: float = 1.0  # 重试基础延迟（秒）
    retry_max_delay: float = 10.0  # 重试最大延迟（秒）
    validate_image_urls: bool = True  # 是否验证图片URL有效性

    # JWT认证配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7天
    refresh_token_expire_days: int = 30

    # ==================== 短信服务配置 ====================

    # 默认短信服务商: tencent, aliyun, mock
    sms_provider: str = "mock"

    # 验证码配置
    verify_code_length: int = 6
    verify_code_expire_minutes: int = 5

    # 短信限流配置
    sms_rate_limit_per_hour: int = 10
    sms_rate_limit_per_minute: int = 1

    # 阿里云短信配置
    aliyun_sms_enabled: bool = False
    aliyun_sms_access_key_id: Optional[str] = None
    aliyun_sms_access_key_secret: Optional[str] = None
    aliyun_sms_sign_name: Optional[str] = None
    aliyun_sms_verify_template: Optional[str] = None  # 验证码短信模板代码
    aliyun_sms_endpoint: str = "dysmsapi.aliyuncs.com"

    # 腾讯云短信配置（已有，保留兼容）
    tencent_sms_secret_id: Optional[str] = None
    tencent_sms_secret_key: Optional[str] = None
    tencent_sms_app_id: Optional[str] = None
    tencent_sms_template_id: Optional[str] = None
    tencent_sms_sign_name: Optional[str] = None

    # 邮件服务配置 (126邮箱) - 已弃用，保留兼容性
    smtp_host: Optional[str] = "smtp.126.com"
    smtp_port: int = 465
    smtp_user: Optional[str] = "lrb1015@126.com"
    smtp_password: Optional[str] = "UCXY4iZsfbTLqEcA"
    smtp_from: Optional[str] = "lrb1015@126.com"
    smtp_use_tls: bool = True  # 126邮箱使用SSL/TLS

    # 微信支付配置
    wechat_appid: Optional[str] = None
    wechat_mch_id: Optional[str] = None
    wechat_api_key: Optional[str] = None
    wechat_cert_path: Optional[str] = None
    wechat_key_path: Optional[str] = None
    wechat_notify_url: Optional[str] = None

    # 支付宝配置
    alipay_app_id: Optional[str] = None
    alipay_private_key: Optional[str] = None
    alipay_public_key: Optional[str] = None
    alipay_notify_url: Optional[str] = None

    # ==================== 数据保留策略配置 ====================

    # 记录保留天数（默认90天=3个月）
    retention_days: int = 90

    # 清理任务运行时间间隔（小时，默认24小时=每天运行一次）
    cleanup_interval_hours: int = 24

    # 清理任务批次大小（每次处理的记录数）
    cleanup_batch_size: int = 100

    # 是否在启动时运行清理（用于测试）
    cleanup_on_startup: bool = False

    # 清理操作是否默认为dry-run模式（仅报告不删除）
    cleanup_dry_run: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=('settings_',)  # 只保护 settings_ 命名空间
    )


# 全局配置实例
settings = Settings()

