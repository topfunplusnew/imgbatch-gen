"""向量数据库管理模块 - 基于内存的简单实现"""

import numpy as np
import httpx
from typing import List, Dict
from loguru import logger


class VectorStore:
    """简单的内存向量存储"""

    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.documents: List[str] = []
        self.embeddings: List[List[float]] = []
        self.metadatas: List[Dict] = []

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap

        return chunks

    async def get_embeddings(self, texts: List[str], api_key: str, base_url: str, model: str = "text-embedding-3-large") -> List[List[float]]:
        """调用中转站获取文本向量（使用 httpx 直接调用）"""
        try:
            url = base_url.rstrip('/') + '/v1/embeddings'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            payload = {'model': model, 'input': texts}

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

            data = resp.json()
            return [item['embedding'] for item in data['data']]

        except Exception as e:
            logger.error(f"获取 embeddings 失败: {e}")
            raise

    async def add_documents(self, texts: List[str], metadatas: List[dict], api_key: str, base_url: str, doc_id_prefix: str = "doc"):
        """添加文档到向量存储"""
        embeddings = await self.get_embeddings(texts, api_key, base_url)

        self.documents.extend(texts)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)

        logger.info(f"已添加 {len(texts)} 个文档块到向量存储")

    async def search(self, query: str, api_key: str, base_url: str, top_k: int = 3) -> List[str]:
        """检索相关文档（余弦相似度）"""
        if not self.embeddings:
            return []

        query_embedding = await self.get_embeddings([query], api_key, base_url)
        query_vec = np.array(query_embedding[0])

        # 计算余弦相似度
        similarities = []
        for emb in self.embeddings:
            doc_vec = np.array(emb)
            similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
            similarities.append(similarity)

        # 获取 top_k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.documents[i] for i in top_indices]
