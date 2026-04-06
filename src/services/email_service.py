"""邮件发送服务"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger

from ..config.settings import settings


class EmailService:
    """邮件发送服务"""

    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.sender = settings.smtp_from or settings.smtp_user
        self.use_tls = settings.smtp_use_tls

    async def send_verify_code(self, to_email: str, code: str) -> bool:
        """发送验证码邮件"""
        subject = f"【{settings.app_name}】邮箱验证码"
        html_body = f"""
        <div style="max-width:480px;margin:0 auto;padding:32px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#333;">
            <div style="text-align:center;margin-bottom:24px;">
                <h2 style="margin:0;color:#8C2A2E;font-size:20px;">{settings.app_name}</h2>
            </div>
            <div style="background:#f9f5f5;border-radius:12px;padding:24px;text-align:center;">
                <p style="margin:0 0 16px;font-size:14px;color:#666;">您的邮箱验证码为：</p>
                <div style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#8C2A2E;margin:16px 0;">
                    {code}
                </div>
                <p style="margin:16px 0 0;font-size:12px;color:#999;">验证码10分钟内有效，请勿泄露给他人</p>
            </div>
            <p style="margin:24px 0 0;font-size:12px;color:#bbb;text-align:center;">如非本人操作，请忽略此邮件</p>
        </div>
        """
        return await self._send_email(to_email, subject, html_body)

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """发送HTML邮件"""
        if not self.host or not self.user or not self.password:
            logger.error("SMTP配置不完整，无法发送邮件")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if self.use_tls and self.port == 465:
                # SSL直连
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=15) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.sender, to_email, msg.as_string())
            else:
                # STARTTLS
                with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.user, self.password)
                    server.sendmail(self.sender, to_email, msg.as_string())

            logger.info(f"邮件发送成功: {to_email}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, error: {e}")
            return False


_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """获取邮件服务实例"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
