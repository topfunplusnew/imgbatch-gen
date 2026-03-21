"""短信服务配置"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SMSProvider(str, Enum):
    """短信服务商类型"""
    TENCENT = "tencent"  # 腾讯云
    ALIYUN = "aliyun"    # 阿里云
    MOCK = "mock"        # 模拟模式（开发测试）


class AliyunSMSConfig(BaseModel):
    """阿里云短信配置"""
    enabled: bool = False
    access_key_id: str = Field(default="", description="阿里云AccessKey ID")
    access_key_secret: str = Field(default="", description="阿里云AccessKey Secret")
    endpoint: str = Field(
        default="dysmsapi.aliyuncs.com",
        description="阿里云短信服务端点"
    )
    sign_name: str = Field(default="", description="短信签名名称")
    verify_code_template: str = Field(default="", description="验证码短信模板代码")


class TencentSMSConfig(BaseModel):
    """腾讯云短信配置"""
    enabled: bool = False
    secret_id: str = Field(default="", description="腾讯云SecretId")
    secret_key: str = Field(default="", description="腾讯云SecretKey")
    app_id: str = Field(default="", description="短信应用ID")
    verify_code_template: str = Field(default="", description="验证码短信模板ID")
    sign_name: str = Field(default="", description="短信签名")


class SMSConfig(BaseModel):
    """短信服务总配置"""
    # 默认使用的服务商
    provider: SMSProvider = Field(
        default=SMSProvider.MOCK,
        description="默认短信服务商"
    )

    # 验证码配置
    verify_code_length: int = Field(
        default=6,
        ge=4,
        le=8,
        description="验证码长度"
    )
    verify_code_expire_minutes: int = Field(
        default=5,
        ge=1,
        le=30,
        description="验证码有效期（分钟）"
    )

    # 限流配置
    rate_limit_per_hour: int = Field(
        default=10,
        ge=1,
        description="每小时同一手机号发送次数限制"
    )
    rate_limit_per_minute: int = Field(
        default=1,
        ge=1,
        description="每分钟同一手机号发送次数限制"
    )

    # 阿里云配置
    aliyun: AliyunSMSConfig = Field(
        default_factory=AliyunSMSConfig,
        description="阿里云短信配置"
    )

    # 腾讯云配置
    tencent: TencentSMSConfig = Field(
        default_factory=TencentSMSConfig,
        description="腾讯云短信配置"
    )

    def get_active_provider(self) -> SMSProvider:
        """获取当前激活的服务商"""
        # 优先检查配置了哪个服务商
        if self.provider != SMSProvider.MOCK:
            return self.provider

        # 自动检测配置的服务商
        if self.aliyun.enabled and self.aliyun.access_key_id and self.aliyun.access_key_secret:
            return SMSProvider.ALIYUN
        if self.tencent.enabled and self.tencent.secret_id and self.tencent.secret_key:
            return SMSProvider.TENCENT

        return SMSProvider.MOCK

    def is_aliyun_available(self) -> bool:
        """检查阿里云是否可用"""
        return (
            self.aliyun.enabled
            and bool(self.aliyun.access_key_id)
            and bool(self.aliyun.access_key_secret)
            and bool(self.aliyun.sign_name)
            and bool(self.aliyun.verify_code_template)
        )

    def is_tencent_available(self) -> bool:
        """检查腾讯云是否可用"""
        return (
            self.tencent.enabled
            and bool(self.tencent.secret_id)
            and bool(self.tencent.secret_key)
            and bool(self.tencent.app_id)
            and bool(self.tencent.verify_code_template)
        )


# 默认配置
DEFAULT_SMS_CONFIG = SMSConfig()


def load_sms_config_from_env() -> SMSConfig:
    """从环境变量加载短信配置"""
    from ..settings import settings

    config = SMSConfig()

    # 从环境变量读取服务商类型
    provider_str = getattr(settings, "sms_provider", "mock").lower()
    if provider_str == "aliyun":
        config.provider = SMSProvider.ALIYUN
    elif provider_str == "tencent":
        config.provider = SMSProvider.TENCENT
    else:
        config.provider = SMSProvider.MOCK

    # 阿里云配置
    config.aliyun.enabled = getattr(settings, "aliyun_sms_enabled", False)
    config.aliyun.access_key_id = getattr(settings, "aliyun_sms_access_key_id", "")
    config.aliyun.access_key_secret = getattr(settings, "aliyun_sms_access_key_secret", "")
    config.aliyun.sign_name = getattr(settings, "aliyun_sms_sign_name", "")
    config.aliyun.verify_code_template = getattr(settings, "aliyun_sms_verify_template", "")

    # 腾讯云配置
    config.tencent.enabled = getattr(settings, "tencent_sms_enabled", False)
    config.tencent.secret_id = getattr(settings, "tencent_sms_secret_id", "")
    config.tencent.secret_key = getattr(settings, "tencent_sms_secret_key", "")
    config.tencent.app_id = getattr(settings, "tencent_sms_app_id", "")
    config.tencent.verify_code_template = getattr(settings, "tencent_sms_template_id", "")
    config.tencent.sign_name = getattr(settings, "tencent_sms_sign_name", "")

    # 验证码配置
    config.verify_code_length = getattr(settings, "verify_code_length", 6)
    config.verify_code_expire_minutes = getattr(settings, "verify_code_expire_minutes", 5)

    # 限流配置
    config.rate_limit_per_hour = getattr(settings, "sms_rate_limit_per_hour", 10)
    config.rate_limit_per_minute = getattr(settings, "sms_rate_limit_per_minute", 1)

    return config


# 全局配置实例
_sms_config: Optional[SMSConfig] = None


def get_sms_config() -> SMSConfig:
    """获取短信配置（单例）"""
    global _sms_config
    if _sms_config is None:
        _sms_config = load_sms_config_from_env()
    return _sms_config


def reset_sms_config():
    """重置短信配置（用于测试或重新加载）"""
    global _sms_config
    _sms_config = None
