"""Embedding语义匹配器基础接口"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import numpy as np

from ..models.image import ImageParams
from .templates import PARAMETER_TEMPLATES


class BaseMatcher(ABC):
    """基础匹配器接口"""
    
    def __init__(self):
        """初始化匹配器"""
        self.templates = PARAMETER_TEMPLATES
        self._template_embeddings = None
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        pass
    
    async def match_template(self, user_input: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        匹配最相似的模板
        
        Args:
            user_input: 用户输入
            top_k: 返回前k个最相似的模板
            
        Returns:
            (模板, 相似度分数) 的列表
        """
        if self._template_embeddings is None:
            await self._precompute_template_embeddings()
        
        user_embedding = await self.get_embedding(user_input)
        user_embedding = np.array(user_embedding)
        
        similarities = []
        for i, template in enumerate(self.templates):
            template_embedding = np.array(self._template_embeddings[i])
            # 计算余弦相似度
            similarity = np.dot(user_embedding, template_embedding) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(template_embedding)
            )
            similarities.append((template, float(similarity)))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def enhance_params(self, params: ImageParams, user_input: str) -> ImageParams:
        """
        使用模板匹配增强参数（已禁用embedding，直接返回原参数）
        """
        return params
    
    async def _precompute_template_embeddings(self):
        """预计算模板的嵌入向量"""
        self._template_embeddings = []
        for template in self.templates:
            # 组合模板的描述和关键词
            text = f"{template['description']} {' '.join(template['keywords'])}"
            embedding = await self.get_embedding(text)
            self._template_embeddings.append(embedding)


