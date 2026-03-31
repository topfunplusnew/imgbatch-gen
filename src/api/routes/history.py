"""对话历史接口."""

from fastapi import APIRouter, Depends, Request

from ..schemas.history import CreateSessionRequest, SaveMessageRequest
from ...services.history_service import HistoryService, _serialize_utc_datetime
from .chat import _extract_api_key, _get_openai_client


router = APIRouter(prefix="/api/v1", tags=["history"])

_history_service = HistoryService()


def _get_history_service() -> HistoryService:
    return _history_service


# ==================== 路由 ====================
def _get_client_id(http_request: Request) -> str:
    """从 Cookie 中获取客户端 ID."""
    return http_request.cookies.get("client_id", "anonymous")


@router.post("/history/create_session")
async def create_session(
    request: CreateSessionRequest,
    http_request: Request,
    service: HistoryService = Depends(_get_history_service),
):
    """
    创建新的对话会话

    当用户开启新对话时调用此接口创建一个新的会话记录。
    """
    return await service.create_session(
        session_id=request.session_id,
        title=request.title,
        model=request.model,
        provider=request.provider,
        client_id=_get_client_id(http_request),
    )


@router.post("/history/save_message")
async def save_message(
    request: SaveMessageRequest,
    service: HistoryService = Depends(_get_history_service),
):
    """
    保存单条消息

    保存用户的单条消息到对话消息表中，关联到对应的会话ID。
    """
    return await service.save_message(
        session_id=request.session_id,
        role=request.role,
        content=request.content,
        model=request.model,
        provider=request.provider,
        images=request.images,
        files=request.files,
        user_request_id=request.user_request_id,
    )


@router.get("/history/list")
async def list_conversations(
    http_request: Request,
    limit: int = 20,
    offset: int = 0,
    service: HistoryService = Depends(_get_history_service),
):
    """
    获取对话列表

    返回当前客户端的对话摘要信息，按创建时间倒序排列。
    """
    return await service.list_conversations(
        client_id=_get_client_id(http_request),
        limit=limit,
        offset=offset,
    )


@router.get("/history/{session_id}")
async def get_conversation(
    session_id: str,
    service: HistoryService = Depends(_get_history_service),
):
    """
    获取特定对话的详细信息

    根据session_id获取对话的所有消息和文件信息。
    消息按创建时间升序排列。
    """
    return await service.get_conversation(session_id=session_id)


@router.delete("/history/{session_id}")
async def delete_conversation(
    session_id: str,
    service: HistoryService = Depends(_get_history_service),
):
    """
    删除特定对话

    根据session_id删除对话会话及其所有相关消息。
    """
    return await service.delete_conversation(session_id=session_id)


@router.post("/history/{session_id}/summary")
async def summarize_conversation(
    session_id: str,
    http_request: Request,
    service: HistoryService = Depends(_get_history_service),
):
    """
    使用 ChatGPT 对当前会话生成总结
    """
    api_key = _extract_api_key(http_request)
    client = await _get_openai_client(api_key)
    return await service.summarize_conversation(session_id=session_id, client=client)
