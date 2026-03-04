"""
Whisper STT Service - 基于 faster-whisper 的本地语音识别
替代百度 STT，提供更准确的英语语音识别
"""
import asyncio
import tempfile
import os
import io
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhisperSTTService:
    """使用 faster-whisper 进行本地语音识别"""
    
    def __init__(self):
        self._model = None
        self._model_name = settings.WHISPER_MODEL
        self._device = settings.WHISPER_DEVICE
        self._compute_type = settings.WHISPER_COMPUTE_TYPE
    
    def _ensure_model(self):
        """懒加载模型（首次调用时加载）"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(
                    f"Loading Whisper model: {self._model_name} "
                    f"(device={self._device}, compute_type={self._compute_type})"
                )
                self._model = WhisperModel(
                    self._model_name,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                logger.info("Whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                # 降级到 CPU
                if self._device == "cuda":
                    logger.warning("Falling back to CPU mode...")
                    from faster_whisper import WhisperModel
                    self._model = WhisperModel(
                        self._model_name,
                        device="cpu",
                        compute_type="int8",
                    )
                    logger.info("Whisper model loaded on CPU (fallback).")
                else:
                    raise
    
    def _transcribe_sync(self, audio_data: bytes) -> str:
        """同步识别（在线程池中运行）"""
        self._ensure_model()
        
        # 将音频数据写入临时文件
        suffix = ".wav"
        # 检查是否是 webm 格式（浏览器 MediaRecorder 默认格式）
        if audio_data[:4] == b'\x1aE\xdf\xa3':
            suffix = ".webm"
        elif audio_data[:4] == b'OggS':
            suffix = ".ogg"
        
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_data)
                tmp_path = f.name
            
            segments, info = self._model.transcribe(
                tmp_path,
                language="en",
                beam_size=5,
                vad_filter=True,  # 过滤静音段，提高准确率
            )
            
            text = " ".join([segment.text for segment in segments]).strip()
            logger.info(f"Whisper STT result: '{text}' (lang={info.language}, prob={info.language_probability:.2f})")
            return text
            
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def transcribe(self, audio_data: bytes) -> str:
        """
        异步语音识别
        
        Args:
            audio_data: 音频二进制数据（支持 WAV, WebM, OGG 等格式）
            
        Returns:
            识别出的英文文本
        """
        if not audio_data:
            raise ValueError("Audio data is empty")
        
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._transcribe_sync, audio_data)
        
        if not text:
            raise ValueError("No speech detected in audio")
        
        return text


# 全局实例
whisper_stt = WhisperSTTService()
