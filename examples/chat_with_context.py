"""对话上下文管理使用示例"""

import asyncio
import httpx


async def chat_example():
    """演示如何使用会话上下文"""
    base_url = "http://localhost:8000"
    session_id = "user_123"

    # 第一轮对话
    response1 = await httpx.AsyncClient().post(
        f"{base_url}/api/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "我想生成一张猫的图片"}
            ],
            "session_id": session_id,
            "enable_context": True
        }
    )
    print("第一轮:", response1.json()["choices"][0]["message"]["content"])

    # 第二轮对话（会自动带上第一轮的上下文）
    response2 = await httpx.AsyncClient().post(
        f"{base_url}/api/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "改成狗"}
            ],
            "session_id": session_id,
            "enable_context": True
        }
    )
    print("第二轮:", response2.json()["choices"][0]["message"]["content"])


if __name__ == "__main__":
    asyncio.run(chat_example())
