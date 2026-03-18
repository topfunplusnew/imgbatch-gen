"""使用LLM生成对话总结"""

from typing import List, Dict, Any
from openai import AsyncOpenAI
from loguru import logger


async def summarize_with_llm(
    messages: List[Dict[str, Any]],
    api_key: str,
    base_url: str = None,
    model: str = "gpt-4o-mini"
) -> str:
    """使用LLM总结对话历史"""
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        # 构建总结提示
        conversation = "\n".join([
            f"{msg['role']}: {msg['content'][:200]}"
            for msg in messages
        ])

        prompt = f"""请简洁总结以下对话的关键内容（100字以内）：

{conversation}

总结："""

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"LLM总结完成：{summary[:50]}...")
        return summary

    except Exception as e:
        logger.error(f"LLM总结失败: {e}")
        return f"讨论了{len(messages)}条消息"
