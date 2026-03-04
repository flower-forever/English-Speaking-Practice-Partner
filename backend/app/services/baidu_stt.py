import httpx
import json
from app.core.config import settings

class BaiduSTTService:
    def __init__(self):
        self.api_key = settings.BAIDU_API_KEY
        self.secret_key = settings.BAIDU_SECRET_KEY
        self.token_url = "https://openapi.baidu.com/oauth/2.0/token"
        self.asr_url = "https://vop.baidu.com/server_api"
        self._token = None
    
    async def get_token(self) -> str:
        """获取访问令牌"""
        if self._token:
            return self._token
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.token_url,
                params={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key
                }
            )
            result = response.json()
            self._token = result.get("access_token")
            return self._token
    
    async def transcribe(self, audio_data: bytes, format: str = "wav", rate: int = 16000) -> str:
        """
        语音识别
        """
        import base64
        
        token = await self.get_token()
        url = f"{self.asr_url}?cuid=baidu_python_client&token={token}&dev_pid=1936&speech={base64.b64encode(audio_data).decode()}&format={format}&rate={rate}&channel=1"
        
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(audio_data))
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, content=audio_data)
            result = response.json()
            
            if result.get("err_no") == 0:
                return result.get("result", [""])[0]
            else:
                raise Exception(f"百度 STT 识别失败：{result.get('err_msg')}")

# 全局实例
baidu_stt = BaiduSTTService()