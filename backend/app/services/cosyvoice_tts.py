"""
CosyVoice TTS Service - 基于阿里云 CosyVoice v3 的流式语音合成
替代旧的 Sambert TTS，支持双向流式合成、中英双语、音色克隆、情感控制
"""
import asyncio
import logging
import queue
import threading
from typing import Optional, AsyncGenerator, Callable

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat, ResultCallback

from app.core.config import settings

logger = logging.getLogger(__name__)


class StreamingTTSCallback(ResultCallback):
    """
    CosyVoice 流式回调：将音频分片推入队列
    """
    
    def __init__(self, audio_queue: queue.Queue):
        super().__init__()
        self._queue = audio_queue
        self._completed = threading.Event()
        self._error: Optional[str] = None
    
    def on_open(self):
        logger.debug("CosyVoice WebSocket connection opened")
    
    def on_data(self, data: bytes) -> None:
        """收到音频分片"""
        if data:
            self._queue.put(data)
    
    def on_complete(self):
        """合成完成"""
        logger.debug("CosyVoice synthesis complete")
        self._queue.put(None)  # 发送结束标记
        self._completed.set()
    
    def on_error(self, message: str):
        """合成出错"""
        logger.error(f"CosyVoice TTS error: {message}")
        self._error = message
        self._queue.put(None)
        self._completed.set()
    
    def on_close(self):
        logger.debug("CosyVoice WebSocket connection closed")
    
    def on_event(self, message):
        pass
    
    @property
    def error(self) -> Optional[str]:
        return self._error
    
    def wait_complete(self, timeout: float = 60.0) -> bool:
        return self._completed.wait(timeout)


class CosyVoiceTTSService:
    """CosyVoice v3 流式语音合成服务"""
    
    def __init__(self):
        # 设置 API Key
        dashscope.api_key = settings.api_key
        self._model = settings.COSYVOICE_MODEL
        self._default_voice = settings.COSYVOICE_DEFAULT_VOICE
    
    def _create_synthesizer(
        self,
        voice: str,
        callback: ResultCallback,
        audio_format: AudioFormat = AudioFormat.MP3_22050HZ_MONO_256KBPS,
    ) -> SpeechSynthesizer:
        """创建流式合成器实例"""
        return SpeechSynthesizer(
            model=self._model,
            voice=voice or self._default_voice,
            format=audio_format,
            callback=callback,
        )
    
    async def synthesize_streaming(
        self,
        text_chunks: AsyncGenerator[str, None],
        voice: str = "",
        on_audio_chunk: Optional[Callable[[bytes], None]] = None,
    ) -> bytes:
        """
        双向流式合成：LLM 文本流 → TTS 音频流
        
        接收 LLM 的增量文本，实时合成音频并通过回调返回音频分片。
        同时收集所有音频用于完整播放。
        
        Args:
            text_chunks: LLM 输出的异步文本流
            voice: 音色名称
            on_audio_chunk: 每收到一个音频分片时的回调
            
        Returns:
            完整的音频数据
        """
        if not voice:
            voice = self._default_voice
            
        audio_queue: queue.Queue = queue.Queue()
        callback = StreamingTTSCallback(audio_queue)
        
        synthesizer = self._create_synthesizer(voice, callback)
        
        all_audio = bytearray()
        loop = asyncio.get_running_loop()
        
        # 在后台线程中消费音频队列
        async def drain_audio():
            """从队列中取出音频分片"""
            while True:
                try:
                    # 非阻塞检查队列
                    chunk = await loop.run_in_executor(
                        None, lambda: audio_queue.get(timeout=0.05)
                    )
                    if chunk is None:
                        break
                    all_audio.extend(chunk)
                    if on_audio_chunk:
                        on_audio_chunk(chunk)
                except Exception:
                    # queue.Empty → 继续等待
                    if callback._completed.is_set():
                        # 排空剩余
                        while not audio_queue.empty():
                            c = audio_queue.get_nowait()
                            if c is None:
                                break
                            all_audio.extend(c)
                            if on_audio_chunk:
                                on_audio_chunk(c)
                        break
        
        # 启动音频收集任务
        audio_task = asyncio.create_task(drain_audio())
        
        # 将 LLM 文本逐段喂给 TTS
        text_buffer = ""
        try:
            async for text_chunk in text_chunks:
                text_buffer += text_chunk
                
                # 按标点分割，积累到足够长度时发送
                if len(text_buffer) > 10 and text_buffer[-1] in ".!?,;:。！？，；：\n":
                    await loop.run_in_executor(
                        None, synthesizer.streaming_call, text_buffer
                    )
                    text_buffer = ""
            
            # 发送剩余文本
            if text_buffer.strip():
                await loop.run_in_executor(
                    None, synthesizer.streaming_call, text_buffer
                )
            
            # 通知合成结束
            await loop.run_in_executor(None, synthesizer.streaming_complete)
            
        except Exception as e:
            logger.error(f"Error during streaming TTS: {e}")
            # 确保合成器关闭
            try:
                await loop.run_in_executor(None, synthesizer.streaming_complete)
            except Exception:
                pass
            raise
        
        # 等待音频收集完成
        await audio_task
        
        if callback.error:
            raise Exception(f"CosyVoice TTS error: {callback.error}")
        
        return bytes(all_audio)
    
    async def synthesize(
        self,
        text: str,
        voice: str = "",
    ) -> bytes:
        """
        非流式合成 - 将完整文本一次性合成为音频（兼容旧接口）
        
        Args:
            text: 要合成的文本
            voice: 音色名称
            
        Returns:
            完整的音频二进制数据
        """
        if not voice:
            voice = self._default_voice
            
        audio_queue: queue.Queue = queue.Queue()
        callback = StreamingTTSCallback(audio_queue)
        
        synthesizer = self._create_synthesizer(voice, callback)
        
        loop = asyncio.get_running_loop()
        
        # 发送全部文本并等待完成
        await loop.run_in_executor(None, synthesizer.streaming_call, text)
        await loop.run_in_executor(None, synthesizer.streaming_complete)
        
        # 收集所有音频
        all_audio = bytearray()
        while not audio_queue.empty():
            chunk = audio_queue.get_nowait()
            if chunk is None:
                break
            all_audio.extend(chunk)
        
        if callback.error:
            raise Exception(f"CosyVoice TTS error: {callback.error}")
        
        if not all_audio:
            raise Exception("CosyVoice TTS returned no audio data")
        
        return bytes(all_audio)


# CosyVoice v3-flash 可用的系统音色
COSYVOICE_VOICES = [
    {"id": "longanyang", "name": "龙安洋 (阳光男声)", "lang": "zh+en"},
    {"id": "longanhuan", "name": "龙安欢 (元气女声)", "lang": "zh+en"},
]

# 全局实例
cosyvoice_tts = CosyVoiceTTSService()
