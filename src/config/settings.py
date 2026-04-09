"""Application settings."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


FIXED_RELAY_BASE_URL = "https://api.yiwuxueshe.cn"
FIXED_CONFIG_API_URL = "https://api.yiwuxueshe.cn/api/pricing_new"


class Settings(BaseSettings):
    """Primary application configuration."""

    app_name: str = "智能体生图应用"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8888

    storage_type: str = "local"
    storage_path: str = "./storage"
    storage_url_prefix: str = "/storage"

    minio_endpoint: str = "121.41.81.114:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "admin123"
    minio_bucket_name: str = "images"
    minio_secure: bool = False
    minio_url_prefix: Optional[str] = "/storage"
    public_base_url: Optional[str] = None

    max_concurrent_tasks: int = 20
    task_timeout: int = 300

    default_image_provider: str = "openai"
    default_llm_provider: str = "relay"
    default_embedding_provider: str = "relay"

    relay_api_key: Optional[str] = None
    credential_encryption_key: Optional[str] = None
    credential_ttl_hours: int = 24
    config_cache_ttl_hours: int = 1

    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_image_model: str = "dall-e-3"

    assistant_text_model: str = "gpt-4o-mini"
    assistant_planner_model: str = "gpt-4o-mini"
    assistant_ocr_model: str = "qwen3-vl-plus"
    assistant_attachment_text_limit: int = 12000
    assistant_pdf_ocr_max_pages: int = 50
    assistant_pdf_native_text_threshold: int = 120

    langchain_pdf_prompt_model: str = "gpt-4o-mini"
    langchain_pdf_max_pages: int = 12
    langchain_pdf_page_char_limit: int = 5000

    stable_diffusion_api_url: str = "http://localhost:7860"
    stable_diffusion_api_key: Optional[str] = None

    baidu_api_key: Optional[str] = None
    baidu_secret_key: Optional[str] = None
    baidu_image_model: str = "ernie-vilg-v2"

    aliyun_api_key: Optional[str] = None
    aliyun_image_model: str = "wanx-v1"

    log_dir: str = "./logs"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/agent_db"
    database_echo: bool = False

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "1234"
    postgres_database: str = "agent_db"

    max_generation_retries: int = 2
    retry_base_delay: float = 1.0
    retry_max_delay: float = 10.0
    generation_retry_base_delay: float = 0.0
    generation_retry_max_delay: float = 0.0
    validate_image_urls: bool = True

    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    refresh_token_expire_days: int = 30

    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    default_admin_phone: Optional[str] = None

    sms_provider: str = "mock"
    verify_code_length: int = 6
    verify_code_expire_minutes: int = 5
    sms_rate_limit_per_hour: int = 10
    sms_rate_limit_per_minute: int = 1

    aliyun_sms_enabled: bool = False
    aliyun_sms_access_key_id: Optional[str] = None
    aliyun_sms_access_key_secret: Optional[str] = None
    aliyun_sms_sign_name: Optional[str] = None
    aliyun_sms_verify_template: Optional[str] = None
    aliyun_sms_endpoint: str = "dysmsapi.aliyuncs.com"

    tencent_sms_secret_id: Optional[str] = None
    tencent_sms_secret_key: Optional[str] = None
    tencent_sms_app_id: Optional[str] = None
    tencent_sms_template_id: Optional[str] = None
    tencent_sms_sign_name: Optional[str] = None

    smtp_host: Optional[str] = "smtp.163.com"
    smtp_port: int = 465
    smtp_user: Optional[str] = "testaimail@163.com"
    smtp_password: Optional[str] = "BNA6D33PjkhpbRFW"
    smtp_from: Optional[str] = "testaimail@163.com"
    smtp_use_tls: bool = True

    wechat_appid: Optional[str] = None  # 应用ID
    wechat_mch_id: Optional[str] = None  # 商户号
    wechat_api_key: Optional[str] = None  # APIv3密钥（32位）
    wechat_cert_serial_no: Optional[str] = None  # 商户API证书序列号
    wechat_key_path: Optional[str] = None  # 商户私钥文件路径
    wechat_notify_url: Optional[str] = None  # 支付回调URL

    # 平台公钥模式（2024年9月后新账户使用）
    wechat_public_key: Optional[str] = None  # 微信支付平台公钥内容
    wechat_public_key_id: Optional[str] = None  # 微信支付平台公钥ID

    alipay_app_id: Optional[str] = None
    alipay_private_key: Optional[str] = None
    alipay_public_key: Optional[str] = None
    alipay_notify_url: Optional[str] = None

    retention_days: int = 90
    cleanup_interval_hours: int = 24
    cleanup_batch_size: int = 100
    cleanup_on_startup: bool = False
    cleanup_dry_run: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    @property
    def relay_base_url(self) -> str:
        return FIXED_RELAY_BASE_URL

    @property
    def config_api_url(self) -> str:
        return FIXED_CONFIG_API_URL


settings = Settings()
