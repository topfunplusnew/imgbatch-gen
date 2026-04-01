"""数据库模型定义"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, BaseModel


class UserRequest(BaseModel):
    """用户请求表"""
    __tablename__ = "user_requests"

    # 用户信息
    user_id = Column(String(100), index=True, comment="用户ID")
    user_ip = Column(String(50), comment="用户IP")
    user_agent = Column(String(500), comment="用户代理")

    # 请求信息
    request_type = Column(String(50), index=True, comment="请求类型: image_generation, chat, etc")
    request_data = Column(JSON, comment="请求参数")

    # 状态信息
    status = Column(String(50), default="pending", comment="状态: pending, processing, completed, failed")
    error_message = Column(Text, comment="错误信息")

    # 关联的生成记录
    generation_records = relationship("ImageGenerationRecord", back_populates="user_request")
    # 关联的对话记录
    chat_conversations = relationship("ChatConversation", back_populates="user_request")

    def __repr__(self):
        return f"<UserRequest(id={self.id}, type={self.request_type}, status={self.status})>"


class ImageGenerationRecord(BaseModel):
    """图片生成记录表"""
    __tablename__ = "image_generation_records"

    # 关联用户请求
    user_request_id = Column(String(36), ForeignKey("user_requests.id"), nullable=False)
    user_request = relationship("UserRequest", back_populates="generation_records")

    # 生成参数
    provider = Column(String(100), comment="Provider名称")
    model = Column(String(100), comment="模型名称")
    prompt = Column(Text, comment="提示词")
    negative_prompt = Column(Text, comment="负面提示词")
    width = Column(Integer, comment="图片宽度")
    height = Column(Integer, comment="图片高度")
    n = Column(Integer, default=1, comment="生成数量")

    # 生成配置
    style = Column(String(50), comment="风格")
    quality = Column(String(50), comment="质量")
    extra_params = Column(JSON, comment="额外参数")

    # 生成结果
    status = Column(String(50), default="pending", comment="生成状态")
    image_urls = Column(JSON, comment="生成的图片URL列表")
    image_paths = Column(JSON, comment="本地图片路径列表")

    # 性能信息
    processing_time = Column(Float, comment="处理耗时（秒）")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")

    # Token使用（如果适用）
    prompt_tokens = Column(Integer, comment="提示词Token数")
    completion_tokens = Column(Integer, comment="完成Token数")
    total_tokens = Column(Integer, comment="总Token数")

    # 调用模式
    call_mode = Column(String(50), comment="调用模式: serial, parallel, batch")

    def __repr__(self):
        return f"<ImageGenerationRecord(id={self.id}, provider={self.provider}, status={self.status})>"


class ChatConversation(BaseModel):
    """对话消息表"""
    __tablename__ = "chat_messages"

    # 关联用户请求
    user_request_id = Column(String(36), ForeignKey("user_requests.id"), nullable=True, comment="关联的用户请求ID")
    user_request = relationship("UserRequest", back_populates="chat_conversations")

    # 关联对话会话
    session_id = Column(String(100), ForeignKey("conversation_sessions.session_id"), nullable=False, comment="会话ID")
    session = relationship("ConversationSession", back_populates="messages")

    # 消息信息
    role = Column(String(50), comment="角色: system, user, assistant")
    content = Column(Text, comment="对话内容")

    # 模型信息
    model = Column(String(100), comment="使用的模型")
    provider = Column(String(100), comment="Provider名称")

    # Token使用
    prompt_tokens = Column(Integer, comment="提示词Token数")
    completion_tokens = Column(Integer, comment="完成Token数")
    total_tokens = Column(Integer, comment="总Token数")

    # 参数
    temperature = Column(Float, comment="温度参数")
    max_tokens = Column(Integer, comment="最大Token数")
    top_p = Column(Float, comment="top_p参数")

    # 图片
    images = Column(Text, nullable=True, comment="图片URL列表(JSON)")

    # 文件
    files = Column(Text, nullable=True, comment="文件信息列表(JSON)")

    def __repr__(self):
        return f"<ChatConversation(id={self.id}, role={self.role}, model={self.model})>"


class ConversationSession(BaseModel):
    """对话会话表"""
    __tablename__ = "conversation_sessions"

    # 会话信息
    session_id = Column(String(100), unique=True, nullable=False, index=True, comment="会话ID")
    client_id = Column(String(100), index=True, comment="客户端Cookie ID，用于区分不同客户端")
    title = Column(String(200), comment="对话标题")
    model = Column(String(100), comment="使用的模型")
    provider = Column(String(100), comment="Provider名称")

    # 状态信息
    status = Column(String(20), default="active", comment="状态: active, completed, deleted")

    # 统计信息
    message_count = Column(Integer, default=0, comment="消息数量")
    image_count = Column(Integer, default=0, comment="图片数量")
    file_count = Column(Integer, default=0, comment="文件数量")

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联消息
    messages = relationship("ChatConversation", back_populates="session")

    def __repr__(self):
        return f"<ConversationSession(id={self.id}, session_id={self.session_id}, title={self.title})>"


class StoredCredential(BaseModel):
    """Encrypted per-user API credential."""
    __tablename__ = "stored_credentials"

    provider = Column(String(50), index=True, nullable=False, default="relay")
    base_url = Column(String(500), comment="凭据对应的Base URL")
    user_id = Column(String(100), index=True, comment="关联用户ID")
    session_id = Column(String(100), index=True, comment="关联会话ID")
    encrypted_api_key = Column(Text, nullable=False, comment="加密后的API Key")
    key_hint = Column(String(32), comment="脱敏后的Key提示")
    status = Column(String(20), default="active", index=True, comment="active/expired/revoked")
    expires_at = Column(DateTime, comment="过期时间")
    last_used_at = Column(DateTime, comment="最近使用时间")

    def __repr__(self):
        return f"<StoredCredential(id={self.id}, provider={self.provider}, key_hint={self.key_hint})>"


class SystemLog(BaseModel):
    """系统日志表"""
    __tablename__ = "system_logs"

    # 日志级别
    level = Column(String(20), index=True, comment="日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    # 日志信息
    module = Column(String(100), index=True, comment="模块名称")
    function = Column(String(100), comment="函数名称")
    message = Column(Text, comment="日志消息")
    details = Column(JSON, comment="详细信息")

    # 关联信息
    user_id = Column(String(100), index=True, comment="关联的用户ID")
    request_id = Column(String(36), ForeignKey("user_requests.id"), comment="关联的请求ID")

    # 异常信息
    exception_type = Column(String(100), comment="异常类型")
    exception_message = Column(Text, comment="异常消息")
    traceback = Column(Text, comment="异常堆栈")

    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, module={self.module})>"


class UploadedFile(BaseModel):
    """上传文件表"""
    __tablename__ = "uploaded_files"

    # 文件基本信息
    original_filename = Column(String(255), comment="原始文件名")
    stored_filename = Column(String(255), unique=True, comment="存储的文件名")
    file_path = Column(String(500), comment="文件存储路径")
    file_url = Column(String(500), comment="文件访问URL")
    file_size = Column(Integer, comment="文件大小（字节）")
    file_type = Column(String(100), comment="文件MIME类型")
    file_extension = Column(String(20), comment="文件扩展名")

    # 文件分类
    category = Column(String(50), default="general", comment="文件分类: image, document, other")

    # 关联信息
    conversation_id = Column(String(100), index=True, comment="关联的对话ID")
    message_id = Column(Integer, index=True, comment="关联的消息ID")

    # 访问控制
    is_public = Column(Boolean, default=False, comment="是否公开访问")

    # 文件状态
    status = Column(String(50), default="active", comment="文件状态: active, deleted, archived")

    def __repr__(self):
        return f"<UploadedFile(id={self.id}, original_name={self.original_filename}, size={self.file_size})>"


class Case(BaseModel):
    """案例表 - 管理员上传的生图案例"""
    __tablename__ = "cases"

    # 基本信息
    title = Column(String(200), nullable=False, comment="案例标题")
    description = Column(Text, comment="案例描述")

    # 行业分类（电商、广告、动漫、室内、logo等）
    category = Column(String(50), nullable=False, index=True, comment="行业分类")
    tags = Column(JSON, comment="标签列表（JSON数组）")

    # 图片信息
    thumbnail_url = Column(String(500), comment="缩略图URL")
    image_url = Column(String(500), comment="完整图片URL")
    image_path = Column(String(500), comment="图片存储路径")

    # 生成参数
    prompt = Column(Text, nullable=False, comment="提示词")
    negative_prompt = Column(Text, comment="负面提示词")

    # 参数配置（JSON格式）
    parameters = Column(JSON, comment="生成参数配置")

    # 模型信息
    provider = Column(String(100), comment="Provider名称")
    model = Column(String(100), comment="模型名称")

    # 状态管理
    is_published = Column(Boolean, default=True, index=True, comment="是否发布")
    sort_order = Column(Integer, default=0, index=True, comment="排序权重")
    view_count = Column(Integer, default=0, comment="浏览次数")
    use_count = Column(Integer, default=0, comment="使用次数")

    # 创建者信息
    created_by = Column(String(100), comment="创建者ID（管理员）")

    def __repr__(self):
        return f"<Case(id={self.id}, title={self.title}, category={self.category})>"
