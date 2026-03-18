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
    storage_type: str = "minio"  # 存储类型: "local" 或 "minio"
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

    # 数据库配置（使用SQLite）
    database_url: str = "sqlite+aiosqlite:///./data/agent.db"
    database_echo: bool = False  # 是否输出SQL日志

    # PostgreSQL数据库配置（可选）
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_database: str = "agent_db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=('settings_',)  # 只保护 settings_ 命名空间
    )


# 全局配置实例
settings = Settings()

