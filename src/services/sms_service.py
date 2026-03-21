"""短信服务 - 支持腾讯云、阿里云和模拟模式"""

import json
from typing import Optional, Dict, Any
from loguru import logger
from enum import Enum

# 导入配置
from ..config.sms_config import get_sms_config, SMSProvider

# 腾讯云SDK
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.sms.v20210111 import sms_client, models
    TENCENTCLOUD_AVAILABLE = True
except ImportError:
    TENCENTCLOUD_AVAILABLE = False
    logger.warning("腾讯云SDK未安装: pip install tencentcloud-sdk-python")


class AliyunSMSService:
    """阿里云短信服务"""

    def __init__(
        self,
        access_key_id: str = None,
        access_key_secret: str = None,
        sign_name: str = None,
        verify_code_template: str = None,
        endpoint: str = "dysmsapi.aliyuncs.com",
    ):
        """
        初始化阿里云短信服务

        Args:
            access_key_id: 阿里云AccessKey ID
            access_key_secret: 阿里云AccessKey Secret
            sign_name: 短信签名名称
            verify_code_template: 验证码短信模板代码
            endpoint: 服务端点
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.verify_code_template = verify_code_template
        self.endpoint = endpoint

        # 如果未提供配置，从配置文件加载
        if not all([access_key_id, access_key_secret]):
            self._load_from_config()

        # 延迟初始化客户端
        self._client = None

    def _load_from_config(self):
        """从配置文件加载"""
        config = get_sms_config()
        if config.is_aliyun_available():
            self.access_key_id = config.aliyun.access_key_id
            self.access_key_secret = config.aliyun.access_key_secret
            self.sign_name = config.aliyun.sign_name
            self.verify_code_template = config.aliyun.verify_code_template
            self.endpoint = config.aliyun.endpoint

    def _get_client(self):
        """获取阿里云短信客户端"""
        if self._client is not None:
            return self._client

        try:
            from alibabacloud_dysmsapi20170525.client import Client as DysmsClient
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_tea_openapi import models
            from alibabacloud_tea_util import models as util_models

            if not all([self.access_key_id, self.access_key_secret]):
                raise ValueError("阿里云 AccessKey 未配置")

            # 创建配置
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
            )
            config.endpoint = self.endpoint

            # 创建客户端
            self._client = DysmsClient(config)

            return self._client

        except ImportError:
            raise RuntimeError("阿里云SDK未安装: pip install alibabacloud-dysmsapi20170525")
        except Exception as e:
            logger.error(f"初始化阿里云短信客户端失败: {str(e)}")
            raise

    async def send_verify_code(
        self,
        phone: str,
        code: str,
        template_code: str = None,
        expire_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        发送短信验证码

        Args:
            phone: 手机号
            code: 验证码
            template_code: 短信模板代码（可选，默认使用配置的模板）
            expire_minutes: 验证码有效期（分钟）

        Returns:
            {"success": bool, "message": str, "request_id": str}
        """
        # 检查配置
        if not all([self.access_key_id, self.access_key_secret, self.sign_name]):
            logger.warning(f"[模拟] 阿里云配置不完整，模拟发送短信到 {phone}: {code}")
            return {
                "success": True,
                "message": "模拟发送成功（配置不完整）",
                "request_id": f"mock_{phone}",
            }

        try:
            from alibabacloud_dysmsapi20170525 import models as dysms_models
            from alibabacloud_tea_util import models as util_models

            client = self._get_client()

            # 构建请求
            request = dysms_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=template_code or self.verify_code_template,
                template_param=f'{{"code":"{code}"}}',
            )

            # 发送短信
            runtime = util_models.RuntimeOptions()
            response = await client.send_sms_with_options_async(request, runtime)

            # 检查响应
            if response.status_code == 200:
                body = response.body
                if body.code == "OK":
                    logger.info(f"阿里云短信发送成功: {phone}, request_id={body.request_id}")
                    return {
                        "success": True,
                        "message": "发送成功",
                        "request_id": body.request_id,
                    }
                else:
                    logger.error(f"阿里云短信发送失败: {phone}, code={body.code}, msg={body.message}")
                    return {
                        "success": False,
                        "message": f"{body.code}: {body.message}",
                        "request_id": body.request_id or "",
                    }
            else:
                logger.error(f"阿里云短信HTTP错误: {response.status_code}")
                return {
                    "success": False,
                    "message": f"HTTP错误: {response.status_code}",
                    "request_id": "",
                }

        except Exception as e:
            logger.error(f"阿里云短信发送异常: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "request_id": "",
            }


class TencentCloudSMSService:
    """腾讯云短信服务"""

    def __init__(
        self,
        secret_id: str = None,
        secret_key: str = None,
        app_id: str = None,
        template_id: str = None,
        sign_name: str = None,
    ):
        """
        初始化腾讯云短信服务

        Args:
            secret_id: 腾讯云SecretId
            secret_key: 腾讯云SecretKey
            app_id: 短信应用ID
            template_id: 短信模板ID
            sign_name: 短信签名
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.app_id = app_id
        self.template_id = template_id
        self.sign_name = sign_name

        # 如果未提供配置，从配置文件加载
        if not all([secret_id, secret_key, app_id]):
            self._load_from_config()

        # 延迟初始化客户端
        self._client = None

    def _load_from_config(self):
        """从配置文件加载"""
        config = get_sms_config()
        if config.is_tencent_available():
            self.secret_id = config.tencent.secret_id
            self.secret_key = config.tencent.secret_key
            self.app_id = config.tencent.app_id
            self.template_id = config.tencent.verify_code_template
            self.sign_name = config.tencent.sign_name

    def _get_client(self):
        """获取短信客户端"""
        if self._client is not None:
            return self._client

        if not TENCENTCLOUD_AVAILABLE:
            raise RuntimeError("腾讯云SDK未安装")

        if not all([self.secret_id, self.secret_key]):
            raise ValueError("腾讯云SecretId和SecretKey未配置")

        try:
            cred = credential.Credential(self.secret_id, self.secret_key)
            http_profile = HttpProfile()
            http_profile.endpoint = "sms.tencentcloudapi.com"
            http_profile.reqMethod = "POST"
            http_profile.reqTimeout = 30

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile

            self._client = sms_client.SmsClient(cred, "ap-guangzhou", client_profile)
            return self._client
        except Exception as e:
            logger.error(f"初始化腾讯云短信客户端失败: {str(e)}")
            raise

    async def send_verify_code(
        self,
        phone: str,
        code: str,
        template_id: str = None,
        expire_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        发送短信验证码

        Args:
            phone: 手机号（不带国家码）
            code: 验证码
            template_id: 短信模板ID（可选，默认使用配置的模板）
            expire_minutes: 验证码有效期（分钟）

        Returns:
            {"success": bool, "message": str, "request_id": str}
        """
        # 模拟模式
        if not TENCENTCLOUD_AVAILABLE or not all([self.secret_id, self.secret_key, self.app_id]):
            logger.warning(f"[模拟] 腾讯云发送短信到 {phone}: {code}")
            return {
                "success": True,
                "message": "模拟发送成功",
                "request_id": f"mock_{phone}_{code}",
            }

        try:
            client = self._get_client()

            # 构建请求参数
            req = models.SendSmsRequest()
            req.PhoneNumberSet = [f"+86{phone}"]
            req.TemplateParamSet = [code, str(expire_minutes)]
            req.TemplateID = template_id or self.template_id
            req.SmsSdkAppId = self.app_id

            # 发送短信
            resp = client.SendSms(req)

            # 检查发送结果
            if resp.Status.Code == "Ok":
                logger.info(f"腾讯云短信发送成功: {phone}, request_id={resp.RequestId}")
                return {
                    "success": True,
                    "message": "发送成功",
                    "request_id": resp.RequestId,
                }
            else:
                logger.error(f"腾讯云短信发送失败: {phone}, code={resp.Status.Code}, msg={resp.Status.Message}")
                return {
                    "success": False,
                    "message": resp.Status.Message,
                    "request_id": resp.RequestId,
                }

        except Exception as e:
            logger.error(f"腾讯云短信发送异常: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "request_id": "",
            }


class MockSMSService:
    """模拟短信服务（开发测试用）"""

    async def send_verify_code(
        self,
        phone: str,
        code: str,
        template_id: str = None,
        expire_minutes: int = 5,
    ) -> Dict[str, Any]:
        """模拟发送短信验证码"""
        logger.info(f"[模拟] 发送短信验证码到 {phone}: {code}")
        return {
            "success": True,
            "message": "模拟发送成功",
            "request_id": f"mock_{phone}",
        }


# 全局服务实例
_sms_service: Optional[object] = None


def get_sms_service():
    """
    获取短信服务实例

    根据配置自动选择：
    1. 如果配置了阿里云，使用阿里云
    2. 如果配置了腾讯云，使用腾讯云
    3. 否则使用模拟服务
    """
    global _sms_service
    if _sms_service is not None:
        return _sms_service

    config = get_sms_config()
    provider = config.get_active_provider()

    try:
        if provider == SMSProvider.ALIYUN:
            logger.info("使用阿里云短信服务")
            _sms_service = AliyunSMSService()
        elif provider == SMSProvider.TENCENT:
            logger.info("使用腾讯云短信服务")
            _sms_service = TencentCloudSMSService()
        else:
            logger.info("使用模拟短信服务（开发模式）")
            _sms_service = MockSMSService()
    except Exception as e:
        logger.warning(f"短信服务初始化失败 ({provider})，降级为模拟服务: {str(e)}")
        _sms_service = MockSMSService()

    return _sms_service


def reset_sms_service():
    """重置短信服务（用于切换服务商或重新初始化）"""
    global _sms_service
    _sms_service = None
