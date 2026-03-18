"""本地Embedding匹配器（sentence-transformers）"""

from typing import List
import numpy as np

from ..config.settings import settings
from ..config.providers import ProviderConfig
from .base import BaseMatcher


class LocalMatcher(BaseMatcher):
    """使用本地sentence-transformers进行语义匹配"""
    
    def __init__(self, config: dict = None):
        """初始化本地匹配器"""
        super().__init__()
        
        if config is None:
            config = ProviderConfig.get_local_embedding_config()
        
        self.model_name = config.get("model") or settings.local_embedding_model
        
        # 延迟加载模型
        self._model = None
    
    def _load_model(self):
        """加载sentence-transformers模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError("请安装sentence-transformers: pip install sentence-transformers")
            except Exception as e:
                raise ValueError(f"加载模型失败: {str(e)}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取本地Embedding"""
        if self._model is None:
            self._load_model()
        
        try:
            # sentence-transformers是同步的，但在异步环境中使用
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            raise ValueError(f"本地Embedding获取失败: {str(e)}")


