"""
Qwen LLM Service - 基于 DashScope OpenAI 兼容接口
支持流式和非流式对话，默认使用 qwen3.5-flash（稀疏 MoE，极速输出）
"""
import logging
from typing import List, Dict, AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class QwenLLMService:
    """阿里云 Qwen LLM 服务"""
    
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
    
    @property
    def client(self) -> AsyncOpenAI:
        """懒初始化 OpenAI 客户端"""
        if self._client is None:
            api_key = settings.api_key
            if not api_key:
                raise ValueError(
                    "DASHSCOPE_API_KEY or ALIYUN_API_KEY not set. "
                    "Please configure it in your .env file."
                )
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        return self._client
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        流式对话 - 逐片段返回 LLM 输出
        
        Args:
            messages: 对话历史
            model: 模型名称，默认使用 config 中的 DEFAULT_LLM_MODEL
            
        Yields:
            增量文本片段
        """
        if not model:
            model = settings.DEFAULT_LLM_MODEL
        
        logger.info(f"Qwen streaming chat: model={model}, messages={len(messages)}")
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000,
                extra_body={"enable_thinking": False},
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Qwen streaming error: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
    ) -> str:
        """
        非流式对话 - 返回完整回复（兼容旧接口）
        
        Args:
            messages: 对话历史
            model: 模型名称
            
        Returns:
            完整的 AI 回复文本
        """
        if not model:
            model = settings.DEFAULT_LLM_MODEL
        
        logger.info(f"Qwen chat: model={model}, messages={len(messages)}")
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                extra_body={"enable_thinking": False},
            )
            
            content = response.choices[0].message.content
            if content:
                return content
            else:
                raise Exception(f"Qwen API returned empty response")
                
        except Exception as e:
            logger.error(f"Qwen chat error: {e}")
            raise


# 可用的 Qwen 模型列表（供前端选择）
QWEN_MODELS = [
    "qwen3.5-flash",
    "qwen3.5-plus",
    "qwen-plus",
    "qwen3-max",
]

# 全局实例
qwen_llm = QwenLLMService()