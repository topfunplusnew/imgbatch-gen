"""下载记录API路由"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from loguru import logger

from ...database import get_db_manager, DownloadRecord
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/download", tags=["下载记录"])


# ==================== 请求模型 ====================


class RecordDownloadRequest(BaseModel):
    """记录下载请求"""
    image_url: str = Field(..., description="图片URL")
    file_name: str = Field(..., description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    request_id: Optional[str] = Field(None, description="关联请求ID")
    consumption_record_id: Optional[str] = Field(None, description="关联消费记录ID")


# ==================== 响应模型 ====================


class DownloadRecordResponse(BaseModel):
    """下载记录响应"""
    id: str
    image_url: str
    file_name: str
    file_size: int
    request_id: str
    consumption_record_id: str
    download_ip: str
    created_at: str


# ==================== 路由 ====================


@router.post("/record", summary="记录下载")
async def record_download(
    request: Request,
    body: RecordDownloadRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    记录用户下载行为

    当用户下载图片时调用此接口，用于统计用户下载记录
    """
    db_manager = get_db_manager()

    record = DownloadRecord(
        user_id=user["id"],
        image_url=body.image_url,
        file_name=body.file_name,
        file_size=body.file_size,
        request_id=body.request_id,
        consumption_record_id=body.consumption_record_id,
        download_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "")[:500],
    )

    await db_manager.create_download_record(record)

    return {"success": True, "message": "下载记录已保存"}


@router.get("/records", response_model=List[DownloadRecordResponse], summary="获取下载记录")
async def get_download_records(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    获取用户下载记录列表

    按时间倒序排列，最新的在前
    """
    db_manager = get_db_manager()
    records = await db_manager.get_user_download_records(user["id"], limit, offset)

    return [
        DownloadRecordResponse(
            id=r.id,
            image_url=r.image_url,
            file_name=r.file_name,
            file_size=r.file_size or 0,
            request_id=r.request_id or "",
            consumption_record_id=r.consumption_record_id or "",
            download_ip=r.download_ip or "",
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]


@router.get("/records/count", summary="获取下载记录总数")
async def get_download_records_count(user: dict = Depends(RequiredAuthDependency())):
    """获取用户下载记录总数"""
    db_manager = get_db_manager()
    count = await db_manager.get_user_download_records_count(user["id"])
    return {"count": count}
