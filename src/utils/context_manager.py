"""对话上下文管理器 - 支持历史总结和上下文延续"""

from typing import List, Dict, Any, Optional
from loguru import logger


class ContextManager:
    """管理对话历史，支持滑动窗口和自动总结"""

    def __init__(self, max_messages: int = 10, summary_threshold: int = 8):
        """
        Args:
            max_messages: 保留的最大消息数
            summary_threshold: 触发总结的消息数阈值
        """
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        self.history: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None

    def add_message(self, role: str, content: str):
        """添加新消息到历史"""
        self.history.append({"role": role, "content": content})

        # 超过阈值时触发总结
        if len(self.history) > self.summary_threshold:
            self._compress_history()

    def get_context(self) -> List[Dict[str, Any]]:
        """获取当前上下文（包含总结和最近消息）"""
        messages = []

        # 如果有总结，添加为系统消息
        if self.summary:
            messages.append({
                "role": "system",
                "content": f"之前的对话总结：{self.summary}"
            })

        # 添加最近的消息
        messages.extend(self.history[-self.max_messages:])

        return messages

    def _compress_history(self):
        """压缩历史记录，生成总结"""
        if len(self.history) <= self.summary_threshold:
            return

        # 保留最近的消息，其余生成总结
        old_messages = self.history[:-self.max_messages]
        self.history = self.history[-self.max_messages:]

        # 简单总结（实际应用中可调用LLM生成）
        self.summary = self._generate_summary(old_messages)
        logger.info(f"历史已压缩，生成总结：{self.summary[:50]}...")

    def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """生成对话总结（简化版）"""
        # 提取关键信息
        topics = []
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"][:100]
                topics.append(content)

        return f"讨论了 {len(topics)} 个话题，包括：" + "；".join(topics[:3])

    def clear(self):
        """清空历史"""
        self.history.clear()
        self.summary = None
