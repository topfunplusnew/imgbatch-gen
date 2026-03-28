"""通知系统API路由

包含管理员端和用户端的通知相关接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ...services.notification_service import get_notification_service
from ...services.media_storage_service import save_uploaded_image
from ...utils.sse_manager import stream_sse
from ..auth import RequiredAuthDependency, get_current_user_optional
import os


# ==================== 路由器 ====================

router = APIRouter(prefix="/api/v1/notifications", tags=["通知系统"])
admin_router = APIRouter(prefix="/api/v1/admin/announcements", tags=["管理员-公告管理"])


# ==================== 请求模型 ====================


class CreateAnnouncementRequest(BaseModel):
    """创建公告请求"""
    title: str = Field(..., min_length=1, max_length=200, description="公告标题")
    content: str = Field(..., min_length=1, description="公告内容（富文本HTML）")
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$", description="优先级")
    announcement_type: str = Field("system", pattern="^(system|maintenance|feature|promotion)$", description="公告类型")
    is_pinned: bool = Field(False, description="是否置顶")
    is_published: bool = Field(True, description="是否立即发布")
    target_audience: str = Field("all", pattern="^(all|users_only|admins_only)$", description="目标受众")
    published_at: Optional[datetime] = Field(None, description="发布时间（立即发布留空）")
    expires_at: Optional[datetime] = Field(None, description="过期时间（可选）")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")


class UpdateAnnouncementRequest(BaseModel):
    """更新公告请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="公告标题")
    content: Optional[str] = Field(None, min_length=1, description="公告内容（富文本HTML）")
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$", description="优先级")
    announcement_type: Optional[str] = Field(None, pattern="^(system|maintenance|feature|promotion)$", description="公告类型")
    is_pinned: Optional[bool] = Field(None, description="是否置顶")
    is_published: Optional[bool] = Field(None, description="是否发布")
    target_audience: Optional[str] = Field(None, pattern="^(all|users_only|admins_only)$", description="目标受众")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")


class UploadCoverImageRequest(BaseModel):
    """上传封面图片请求"""
    pass  # 使用 multipart/form-data


# ==================== 响应模型 ====================


class AnnouncementResponse(BaseModel):
    """公告响应"""
    id: str
    title: str
    content: str
    priority: str
    announcement_type: str
    is_pinned: bool
    is_published: bool
    published_at: Optional[str]
    expires_at: Optional[str]
    cover_image_url: Optional[str]
    target_audience: str
    view_count: int
    click_count: int
    created_at: str
    updated_at: str
    created_by: Optional[str]


class NotificationListItemResponse(BaseModel):
    """通知列表项响应"""
    id: str
    title: str
    content: str
    priority: str
    announcement_type: str
    is_pinned: bool
    cover_image_url: Optional[str]
    published_at: Optional[str]
    is_read: bool
    read_at: Optional[str]


class UnreadCountResponse(BaseModel):
    """未读数量响应"""
    count: int


# ==================== 管理员端点 ====================


@admin_router.get("", response_model=dict)
async def list_announcements(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    announcement_type: Optional[str] = Query(None, description="类型筛选"),
    is_published: Optional[bool] = Query(None, description="发布状态筛选"),
    target_audience: Optional[str] = Query(None, description="目标受众筛选"),
    user: dict = Depends(RequiredAuthDependency()),
):
    """获取公告列表（管理员）"""
    # 验证管理员权限
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_notification_service()
    return await service.list_announcements(
        page=page,
        page_size=page_size,
        priority=priority,
        announcement_type=announcement_type,
        is_published=is_published,
        target_audience=target_audience,
    )


@admin_router.post("", response_model=AnnouncementResponse, status_code=201)
async def create_announcement(
    data: CreateAnnouncementRequest,
    user: dict = Depends(RequiredAuthDependency()),
):
    """创建公告"""
    logger.info(f"[Create Announcement] User: {user.get('id')}, Role: {user.get('role')}")

    # 验证管理员权限
    if user.get("role") != "admin":
        logger.warning(f"[Create Announcement] Permission denied for user {user.get('id')} with role {user.get('role')}")
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_notification_service()
    announcement = await service.create_announcement(
        data=data.dict(),
        admin_id=user["id"]
    )

    logger.info(f"[Create Announcement] Success: id={announcement.id}, title={data.title}")
    return AnnouncementResponse(**announcement.to_dict())


@admin_router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    user: dict = Depends(RequiredAuthDependency()),
):
    """获取公告详情（管理员）"""
    # 验证管理员权限
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_notification_service()
    announcement = await service.get_announcement(announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    return AnnouncementResponse(**announcement.to_dict())


@admin_router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: str,
    data: UpdateAnnouncementRequest,
    user: dict = Depends(RequiredAuthDependency()),
):
    """更新公告"""
    logger.info(f"[Update Announcement] User: {user.get('id')}, Role: {user.get('role')}, Announcement: {announcement_id}")

    # 验证管理员权限
    if user.get("role") != "admin":
        logger.warning(f"[Update Announcement] Permission denied for user {user.get('id')} with role {user.get('role')}")
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_notification_service()
    # 过滤None值
    update_data = {k: v for k, v in data.dict().items() if v is not None}

    announcement = await service.update_announcement(
        announcement_id=announcement_id,
        data=update_data,
        admin_id=user["id"]
    )

    if not announcement:
        logger.warning(f"[Update Announcement] Announcement not found: {announcement_id}")
        raise HTTPException(status_code=404, detail="公告不存在")

    logger.info(f"[Update Announcement] Success: id={announcement_id}")
    return AnnouncementResponse(**announcement.to_dict())


@admin_router.delete("/{announcement_id}", status_code=204)
async def delete_announcement(
    announcement_id: str,
    user: dict = Depends(RequiredAuthDependency()),
):
    """删除公告"""
    # 验证管理员权限
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_notification_service()
    success = await service.delete_announcement(announcement_id)

    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")

    return None


@admin_router.post("/{announcement_id}/publish", response_model=AnnouncementResponse)
async def publish_announcement(
    announcement_id: str,
    user: dict = Depends(RequiredAuthDependency()),
):
    """发布公告"""
    # 验证管理员权限
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_notification_service()
    announcement = await service.publish_announcement(announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    return AnnouncementResponse(**announcement.to_dict())


@admin_router.post("/{announcement_id}/upload-cover", status_code=201)
async def upload_cover_image(
    announcement_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(RequiredAuthDependency()),
):
    """上传公告封面图片"""
    # 验证管理员权限
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    # 验证文件类型
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = os.path.splitext(file.filename or "")[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的图片类型: {file_extension}")

    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    # 检查文件大小（限制5MB）
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")

    await file.seek(0)
    image_info = await save_uploaded_image(
        file,
        storage_task_id=f"announcements/{announcement_id}",
        prompt=f"announcement-cover-{announcement_id}",
    )

    # 更新公告
    service = get_notification_service()
    announcement = await service.update_announcement(
        announcement_id=announcement_id,
        data={
            "cover_image_url": image_info["image_url"],
            "cover_image_path": image_info["image_path"],
        },
        admin_id=user["id"]
    )

    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    logger.info(f"上传公告封面成功: {image_info['image_path']}")

    return {
        "url": image_info["image_url"],
        "filename": os.path.basename(image_info["image_path"]),
    }


# ==================== 用户端点 ====================


@router.get("/my", response_model=dict)
async def get_my_notifications(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
):
    """获取我的通知列表"""
    # 获取当前用户（可选）
    user = await get_current_user_optional(request)

    if not user:
        # 未登录用户返回空列表
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    service = get_notification_service()
    return await service.get_my_notifications(
        user_id=user["id"],
        user_role=user.get("role", "user"),
        page=page,
        page_size=page_size,
        is_read=is_read,
    )


@router.get("/my/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(request: Request):
    """获取未读通知数量"""
    # 获取当前用户（可选）
    user = await get_current_user_optional(request)

    if not user:
        return UnreadCountResponse(count=0)

    service = get_notification_service()
    count = await service.get_unread_count(
        user_id=user["id"],
        user_role=user.get("role", "user")
    )

    return UnreadCountResponse(count=count)


@router.post("/my/{announcement_id}/read", status_code=204)
async def mark_as_read(
    announcement_id: str,
    request: Request,
):
    """标记通知为已读"""
    # 获取当前用户（必须登录）
    user = await get_current_user_optional(request)

    if not user:
        raise HTTPException(status_code=401, detail="需要登录")

    service = get_notification_service()
    success = await service.mark_as_read(user_id=user["id"], announcement_id=announcement_id)

    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")

    return None


@router.post("/my/read-all", status_code=204)
async def mark_all_as_read(request: Request):
    """标记所有通知为已读"""
    # 获取当前用户（必须登录）
    user = await get_current_user_optional(request)

    if not user:
        raise HTTPException(status_code=401, detail="需要登录")

    service = get_notification_service()
    count = await service.mark_all_as_read(user_id=user["id"])

    return None


@router.post("/my/{announcement_id}/click", status_code=204)
async def mark_as_clicked(
    announcement_id: str,
    request: Request,
):
    """标记通知为已点击"""
    # 获取当前用户（必须登录）
    user = await get_current_user_optional(request)

    if not user:
        raise HTTPException(status_code=401, detail="需要登录")

    service = get_notification_service()
    success = await service.mark_as_clicked(user_id=user["id"], announcement_id=announcement_id)

    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")

    return None


@router.delete("/my/{announcement_id}", status_code=204)
async def dismiss_notification(
    announcement_id: str,
    request: Request,
):
    """忽略/删除通知"""
    # 获取当前用户（必须登录）
    user = await get_current_user_optional(request)

    if not user:
        raise HTTPException(status_code=401, detail="需要登录")

    service = get_notification_service()
    success = await service.dismiss_notification(user_id=user["id"], announcement_id=announcement_id)

    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")

    return None


@router.get("/stream")
async def notification_stream(request: Request):
    """SSE通知流

    建立Server-Sent Events连接，接收实时通知推送
    """
    # 添加详细日志用于调试
    token_from_cookie = request.cookies.get("access_token")
    token_from_query = request.query_params.get("token")
    logger.info(f"[SSE] Connection attempt - Cookie: {bool(token_from_cookie)}, Query: {bool(token_from_query)}")

    # 获取当前用户（必须登录）
    user = await get_current_user_optional(request)

    if not user:
        logger.warning(f"[SSE] Authentication failed - Cookie: {bool(token_from_cookie)}, Query: {bool(token_from_query)}")
        raise HTTPException(status_code=401, detail="需要登录")

    # 验证用户ID存在
    if not user.get("id"):
        logger.error(f"[SSE] Invalid user info: {user}")
        raise HTTPException(status_code=401, detail="无效的用户信息")

    logger.info(f"[SSE] ✅ Connection established for user: {user['id']}")

    return StreamingResponse(
        stream_sse(request, user["id"]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )


@router.get("/public", response_model=dict)
async def get_public_announcements(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
):
    """获取公开公告列表（未登录用户可访问）"""
    # 获取当前用户（可选）
    user = await get_current_user_optional(request)
    user_role = user.get("role", "user") if user else "guest"
    user_id = user.get("id") if user else None

    print(f"[DEBUG] /public endpoint called - user_role: {user_role}, user_id: {user_id}")

    service = get_notification_service()

    # 使用 get_my_notifications 方法
    result = await service.get_my_notifications(
        user_id=user_id or "guest",  # 传None也可以
        user_role=user_role,
        page=page,
        page_size=page_size,
    )

    print(f"[DEBUG] /public result: {result.get('total', 0)} items")
    for item in result.get('items', []):
        print(f"[DEBUG]   - {item.get('title')}: is_published={item.get('is_published')}, published_at={item.get('published_at')}, target_audience={item.get('target_audience')}")

    return result


@router.get("/public/{announcement_id}", response_model=AnnouncementResponse)
async def get_public_announcement(
    announcement_id: str,
    request: Request,
):
    """获取公开公告详情（未登录用户可访问）"""
    service = get_notification_service()
    announcement = await service.get_announcement(announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    # 检查是否已发布
    if not announcement.is_published:
        raise HTTPException(status_code=404, detail="公告不存在")

    # 检查是否过期
    if announcement.expires_at and announcement.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="公告不存在")

    # 增加浏览次数
    await service.increment_view_count(announcement_id)

    return AnnouncementResponse(**announcement.to_dict())
