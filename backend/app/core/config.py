from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # DashScope API Key (sk- 开头，主要认证方式)
    DASHSCOPE_API_KEY: str = ""
    
    # 向后兼容
    ALIYUN_API_KEY: str = ""
    ALIYUN_APP_ID: str = ""
    
    # 阿里云 AccessKey (用于 AK/SK 认证)
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = ""
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: str = ""
    
    # Whisper STT 配置
    WHISPER_MODEL: str = "small"           # tiny / base / small / medium
    WHISPER_DEVICE: str = "cuda"           # cuda / cpu
    WHISPER_COMPUTE_TYPE: str = "float16"  # float16 / int8
    
    # CosyVoice TTS 配置
    COSYVOICE_MODEL: str = "cosyvoice-v3-flash"
    COSYVOICE_DEFAULT_VOICE: str = "longanyang"
    
    # LLM 默认配置
    DEFAULT_LLM_MODEL: str = "qwen3.5-flash"
    
    # Ollama 配置
    OLLAMA_URL: str = "http://localhost:11434"
    
    # 百度 (已弃用)
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""
    
    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    @property
    def api_key(self) -> str:
        """获取有效的 DashScope API Key"""
        return self.DASHSCOPE_API_KEY or self.ALIYUN_API_KEY
    
    class Config:
        env_file = ".env"

settings = Settings()