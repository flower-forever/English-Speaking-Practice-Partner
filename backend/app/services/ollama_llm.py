"""
Ollama LLM Service - 本地 Ollama 模型服务
支持流式和非流式对话
"""
import httpx
import json
import logging
from typing import List, Dict, AsyncGenerator

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """本地 Ollama LLM 服务"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self._client: httpx.AsyncClient | None = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """复用 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3",
    ) -> AsyncGenerator[str, None]:
        """
        流式对话 - 逐片段返回输出
        
        Args:
            messages: 对话历史
            model: 模型名称
            
        Yields:
            增量文本片段
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
            },
        }
        
        logger.info(f"Ollama streaming chat: model={model}, messages={len(messages)}")
        
        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            text = chunk["message"]["content"]
                            if text:
                                yield text
                        # Ollama 会发送 done=true 的最后一条
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except httpx.ConnectError:
            raise Exception(
                f"无法连接到 Ollama 服务，请确保 Ollama 正在运行 ({self.base_url})"
            )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3",
    ) -> str:
        """
        非流式对话 - 返回完整回复（兼容旧接口）
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
            },
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            else:
                raise Exception(f"Ollama 返回异常：{result}")
        except httpx.ConnectError:
            raise Exception(
                f"无法连接到 Ollama 服务，请确保 Ollama 正在运行 ({self.base_url})"
            )
    
    async def list_models(self) -> List[str]:
        """获取本地安装的所有 Ollama 模型"""
        url = f"{self.base_url}/api/tags"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except httpx.ConnectError:
            return []


# 全局实例
ollama_llm = OllamaService()