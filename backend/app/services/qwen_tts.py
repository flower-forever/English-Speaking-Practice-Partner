import dashscope
from app.core.config import settings

class QwenTTSService:
    def __init__(self):
        dashscope.api_key = settings.ALIYUN_API_KEY
    
    async def synthesize(self, text: str, voice: str = "sambert-zhichu-v1", format: str = "mp3") -> bytes:
        """
        文字转语音
        
        Args:
            text: 要转换的文字
            voice: 音色名称，默认为 sambert-zhichu-v1
            format: 输出格式 (mp3, wav)
            
        Returns:
            音频文件二进制数据
        """
        # Note: If the voice parameter doesn't include "sambert" or "cosyvoice", 
        # we might need to adjust it to match an actual available model/voice id
        # For this basic implementation we will use the model parameter as voice
        model_name = voice if voice.startswith("sambert") else "sambert-zhichu-v1"
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        # Run the synchronous SDK call in an executor
        def _call_tts():
            return dashscope.audio.tts.SpeechSynthesizer.call(
                model=model_name,
                text=text,
                sample_rate=48000,
                format=format
            )
            
        result = await loop.run_in_executor(None, _call_tts)
        
        audio_data = result.get_audio_data()
        if audio_data is not None:
            return audio_data
        else:
            raise Exception(f"阿里云 TTS 合成失败：{result}")

# 全局实例
qwen_tts = QwenTTSService()