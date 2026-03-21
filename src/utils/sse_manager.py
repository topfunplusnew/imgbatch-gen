"""SSE (Server-Sent Events) 连接管理器

用于实时推送通知给客户端
"""

import asyncio
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime
from loguru import logger
from fastapi import Request
from collections import defaultdict


class SSEConnection:
    """SSE连接实例"""

    def __init__(self, user_id: str, queue: asyncio.Queue):
        self.user_id = user_id
        self.queue = queue
        self.connected_at = datetime.utcnow()
        self.last_ping_at = datetime.utcnow()

    async def send(self, data: dict, event_type: str = "message"):
        """发送消息到客户端"""
        message = {
            "event": event_type,
            "data": json.dumps(data, ensure_ascii=False),
            "id": str(int(datetime.utcnow().timestamp() * 1000)),
        }
        await self.queue.put(message)

    async def ping(self):
        """发送心跳保活"""
        self.last_ping_at = datetime.utcnow()
        await self.queue.put({"event": "keepalive", "data": ":keepalive", "id": ""})


class SSEManager:
    """SSE连接管理器

    管理所有活跃的SSE连接，支持广播和定向推送
    """

    def __init__(self):
        # user_id -> set of queues
        self._connections: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        # queue -> user_id mapping (reverse lookup)
        self._queue_to_user: Dict[asyncio.Queue, str] = {}
        # queue -> connection mapping
        self._queue_to_connection: Dict[asyncio.Queue, SSEConnection] = {}
        self._lock = asyncio.Lock()
        self._ping_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """启动SSE管理器（后台心跳任务）"""
        if self._running:
            return

        self._running = True
        self._ping_task = asyncio.create_task(self._ping_loop())
        logger.info("SSE管理器已启动")

    async def stop(self):
        """停止SSE管理器"""
        self._running = False
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        logger.info("SSE管理器已停止")

    async def _ping_loop(self):
        """心跳循环，每30秒发送一次心跳"""
        while self._running:
            try:
                await asyncio.sleep(30)
                await self._send_ping_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE心跳发送失败: {str(e)}")

    async def _send_ping_all(self):
        """向所有连接发送心跳"""
        async with self._lock:
            dead_queues = []
            for queue, connection in self._queue_to_connection.items():
                try:
                    await connection.ping()
                except Exception:
                    dead_queues.append(queue)

            # 清理死连接
            for queue in dead_queues:
                await self._remove_queue(queue)

    async def connect(self, user_id: str) -> asyncio.Queue:
        """创建新的SSE连接

        Args:
            user_id: 用户ID

        Returns:
            asyncio.Queue: 消息队列
        """
        queue = asyncio.Queue()
        connection = SSEConnection(user_id, queue)

        async with self._lock:
            self._connections[user_id].add(queue)
            self._queue_to_user[queue] = user_id
            self._queue_to_connection[queue] = connection

        logger.info(f"SSE连接建立: user_id={user_id}")
        return queue

    async def disconnect(self, queue: asyncio.Queue):
        """断开SSE连接"""
        await self._remove_queue(queue)

    async def _remove_queue(self, queue: asyncio.Queue):
        """移除队列"""
        async with self._lock:
            user_id = self._queue_to_user.pop(queue, None)
            if user_id:
                self._connections[user_id].discard(queue)
                if not self._connections[user_id]:
                    del self._connections[user_id]

            self._queue_to_connection.pop(queue, None)

    async def send_to_user(self, user_id: str, data: dict, event_type: str = "message"):
        """向指定用户发送消息

        Args:
            user_id: 用户ID
            data: 消息数据
            event_type: 事件类型
        """
        async with self._lock:
            queues = self._connections.get(user_id, set())
            if not queues:
                return False

            dead_queues = []
            sent = False
            for queue in queues:
                try:
                    connection = self._queue_to_connection.get(queue)
                    if connection:
                        await connection.send(data, event_type)
                        sent = True
                except Exception as e:
                    logger.warning(f"发送SSE消息失败: {str(e)}")
                    dead_queues.append(queue)

            # 清理死连接
            for queue in dead_queues:
                await self._remove_queue(queue)

            return sent

    async def broadcast(self, data: dict, event_type: str = "message", exclude_user_id: Optional[str] = None):
        """向所有连接广播消息

        Args:
            data: 消息数据
            event_type: 事件类型
            exclude_user_id: 排除的用户ID（不发送给该用户）
        """
        async with self._lock:
            dead_queues = []
            total_sent = 0

            for queue, connection in self._queue_to_connection.items():
                # 排除指定用户
                if exclude_user_id and connection.user_id == exclude_user_id:
                    continue

                try:
                    await connection.send(data, event_type)
                    total_sent += 1
                except Exception as e:
                    logger.warning(f"广播SSE消息失败: {str(e)}")
                    dead_queues.append(queue)

            # 清理死连接
            for queue in dead_queues:
                await self._remove_queue(queue)

            logger.debug(f"SSE广播完成，发送给 {total_sent} 个连接")
            return total_sent

    async def broadcast_to_role(self, role: str, data: dict, event_type: str = "message"):
        """向特定角色的用户广播消息

        Args:
            role: 用户角色 (user, admin)
            data: 消息数据
            event_type: 事件类型
        """
        # 需要从数据库获取用户列表
        from ..database import get_db_manager, User
        from sqlalchemy import select

        db_manager = get_db_manager()
        user_ids = set()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(User.id).where(User.role == role).where(User.status == "active")
            )
            user_ids = {row[0] for row in result.all()}

        # 向这些用户发送
        async with self._lock:
            dead_queues = []
            total_sent = 0

            for queue, connection in self._queue_to_connection.items():
                if connection.user_id not in user_ids:
                    continue

                try:
                    await connection.send(data, event_type)
                    total_sent += 1
                except Exception as e:
                    logger.warning(f"广播SSE消息失败: {str(e)}")
                    dead_queues.append(queue)

            # 清理死连接
            for queue in dead_queues:
                await self._remove_queue(queue)

            logger.debug(f"SSE角色广播完成，发送给 {total_sent} 个 {role} 连接")
            return total_sent

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._queue_to_connection)

    def get_user_connection_count(self, user_id: str) -> int:
        """获取指定用户的连接数"""
        return len(self._connections.get(user_id, set()))


# 全局SSE管理器实例
_sse_manager: Optional[SSEManager] = None


def get_sse_manager() -> SSEManager:
    """获取全局SSE管理器实例"""
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEManager()
    return _sse_manager


async def stream_sse(request: Request, user_id: str):
    """SSE流生成器

    用于FastAPI的StreamingResponse

    Args:
        request: FastAPI请求对象
        user_id: 用户ID
    """
    sse_manager = get_sse_manager()
    queue = await sse_manager.connect(user_id)

    logger.info(f"[SSE] Stream started for user: {user_id}")

    try:
        while True:
            # 检查客户端是否断开
            if await request.is_disconnected():
                logger.info(f"[SSE] Client disconnected: user_id={user_id}")
                break

            try:
                # 等待消息，超时后发送心跳
                message = await asyncio.wait_for(queue.get(), timeout=1.0)

                # 格式化SSE消息
                event = message.get("event", "message")
                data = message.get("data", "")
                msg_id = message.get("id", "")

                lines = []
                if event:
                    lines.append(f"event: {event}")
                if msg_id:
                    lines.append(f"id: {msg_id}")
                lines.append(f"data: {data}")
                lines.append("")

                yield "\n".join(lines) + "\n"
                logger.debug(f"[SSE] Message sent to {user_id}: event={event}")

            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                logger.error(f"[SSE] Stream error for {user_id}: {str(e)}")
                break

    finally:
        await sse_manager.disconnect(queue)
        logger.info(f"[SSE] Stream cleaned up for user: {user_id}")
