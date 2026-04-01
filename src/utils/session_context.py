"""多会话上下文管理 - 支持LLM总结和滑动窗口"""

from typing import Dict, List, Any, Optional
from loguru import logger

from .llm_summarizer import summarize_with_llm


class SessionContextManager:
    """管理多个会话的上下文，每个 session_id 独立维护历史"""

    def __init__(self, max_messages: int = 10, summary_threshold: int = 8):
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        # session_id -> {"history": [...], "summary": str|None}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _ensure_session(self, session_id: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = {"history": [], "summary": None}

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到指定会话"""
        self._ensure_session(session_id)
        self._sessions[session_id]["history"].append({"role": role, "content": content})

    async def get_context_messages(
        self,
        session_id: str,
        new_messages: List[Dict[str, Any]],
        api_key: str = None,
        base_url: str = None,
        summary_model: str = "gpt-4o-mini",
    ) -> List[Dict[str, Any]]:
        """
        获取带上下文的完整消息列表。
        将历史总结 + 近期历史 + 本次新消息合并返回。
        如果历史过长，自动触发LLM总结压缩。
        """
        self._ensure_session(session_id)
        session = self._sessions[session_id]

        # 检查是否需要压缩
        if len(session["history"]) > self.summary_threshold and api_key:
            await self._compress(session_id, api_key, base_url, summary_model)

        result = []

        # 1. 添加历史总结
        if session["summary"]:
            result.append({
                "role": "system",
                "content": f"之前的对话总结：{session['summary']}"
            })

        # 2. 添加近期历史
        recent = session["history"][-self.max_messages:]
        result.extend(recent)

        # 3. 添加本次新消息（排除已在历史中的）
        for msg in new_messages:
            if msg not in result:
                result.append(msg)

        return result

    async def _compress(
        self, session_id: str, api_key: str, base_url: str, model: str
    ):
        """压缩历史，使用LLM生成总结"""
        session = self._sessions[session_id]
        old_messages = session["history"][:-self.max_messages]

        if not old_messages:
            return

        # 如果已有总结，把旧总结也加入待总结内容
        if session["summary"]:
            old_messages.insert(0, {
                "role": "system",
                "content": f"更早的总结：{session['summary']}"
            })

        session["summary"] = await summarize_with_llm(
            old_messages, api_key, base_url, model
        )
        session["history"] = session["history"][-self.max_messages:]
        logger.info(f"会话 {session_id} 历史已压缩")

    def record_exchange(self, session_id: str, user_content: str, assistant_content: str):
        """记录一轮完整的对话交换"""
        self.add_message(session_id, "user", user_content)
        self.add_message(session_id, "assistant", assistant_content)

    def clear_session(self, session_id: str):
        """清空指定会话"""
        self._sessions.pop(session_id, None)

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())


# 全局单例
session_manager = SessionContextManager()
