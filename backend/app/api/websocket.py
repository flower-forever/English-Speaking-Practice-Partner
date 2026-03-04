"""
WebSocket 实时语音对话 - 流式管线
STT(whisper) → LLM(streaming) → TTS(CosyVoice streaming) → 前端分片播放
"""
import asyncio
import json
import logging
import queue
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.whisper_stt import whisper_stt
from app.services.qwen_llm import qwen_llm
from app.services.ollama_llm import ollama_llm
from app.services.cosyvoice_tts import cosyvoice_tts
from app.api.scenes import _load_scene
from app.services.scene_context import SceneContextService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 对话历史最大轮数（防止 context 过长）
MAX_HISTORY_TURNS = 20


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    实时语音对话 WebSocket
    
    协议消息类型：
    
    客户端 → 服务端:
        - bytes: 音频数据（WebM/WAV）
        - {"type": "config", ...}: 配置更新
        - {"type": "message", "content": "..."}: 文字消息
        - {"type": "clear_history"}: 清空历史
    
    服务端 → 客户端:
        - {"type": "stt_result", "text": "..."}: 语音识别结果
        - {"type": "llm_chunk", "text": "..."}: LLM 增量文本
        - {"type": "llm_done"}: LLM 生成结束
        - bytes: TTS 音频分片
        - {"type": "complete"}: 整轮对话完成
        - {"type": "error", "message": "..."}: 错误信息
    """
    await websocket.accept()
    
    # 会话状态
    conversation_history: list[dict] = []
    current_voice = settings.COSYVOICE_DEFAULT_VOICE
    current_scene_id: Optional[str] = None
    current_model = settings.DEFAULT_LLM_MODEL
    current_provider = "aliyun"
    
    logger.info("WebSocket client connected")
    
    try:
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                # ===== 收到音频数据 → 启动 STT → LLM → TTS 流式管线 =====
                audio_data = data["bytes"]
                
                try:
                    # 1. STT: 语音转文字 (faster-whisper)
                    user_text = await whisper_stt.transcribe(audio_data)
                    
                    await websocket.send_json({
                        "type": "stt_result",
                        "text": user_text,
                    })
                    
                    # 2 & 3. 流式 LLM + TTS
                    await _streaming_pipeline(
                        websocket=websocket,
                        user_text=user_text,
                        conversation_history=conversation_history,
                        provider=current_provider,
                        model=current_model,
                        voice=current_voice,
                    )
                    
                except Exception as e:
                    logger.error(f"Audio pipeline error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })
            
            elif "text" in data:
                text_data = json.loads(data["text"])
                msg_type = text_data.get("type")
                
                if msg_type == "config":
                    # ===== 配置更新 =====
                    if text_data.get("voice"):
                        current_voice = text_data["voice"]
                    if text_data.get("provider"):
                        current_provider = text_data["provider"]
                    if text_data.get("model"):
                        current_model = text_data["model"]
                    
                    if text_data.get("scene_id"):
                        current_scene_id = text_data["scene_id"]
                        scene = _load_scene(current_scene_id)
                        if scene:
                            scene_service = SceneContextService(scene)
                            system_prompt = scene_service.get_system_prompt()
                            conversation_history = [
                                {"role": "system", "content": system_prompt}
                            ]
                            logger.info(f"Scene '{current_scene_id}' loaded")
                
                elif msg_type == "message":
                    # ===== 文字消息 → LLM + TTS 流式 =====
                    if text_data.get("voice"):
                        current_voice = text_data["voice"]
                    if text_data.get("provider"):
                        current_provider = text_data["provider"]
                    if text_data.get("model"):
                        current_model = text_data["model"]
                    
                    user_text = text_data.get("content", "")
                    if not user_text.strip():
                        continue
                    
                    try:
                        await _streaming_pipeline(
                            websocket=websocket,
                            user_text=user_text,
                            conversation_history=conversation_history,
                            provider=current_provider,
                            model=current_model,
                            voice=current_voice,
                        )
                    except Exception as e:
                        logger.error(f"Text pipeline error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e),
                        })
                
                elif msg_type == "clear_history":
                    # ===== 清空历史 =====
                    if current_scene_id:
                        scene = _load_scene(current_scene_id)
                        if scene:
                            scene_service = SceneContextService(scene)
                            system_prompt = scene_service.get_system_prompt()
                            conversation_history = [
                                {"role": "system", "content": system_prompt}
                            ]
                    else:
                        conversation_history = []
                    
                    await websocket.send_json({"type": "history_cleared"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")


async def _streaming_pipeline(
    websocket: WebSocket,
    user_text: str,
    conversation_history: list[dict],
    provider: str,
    model: str,
    voice: str,
):
    """
    流式管线核心：LLM 流式生成 → 文本分片 → TTS 流式合成 → 音频分片实时发送
    
    关键改进：音频分片在 TTS 回调中实时推送到前端，而不是等全部生成完再发送。
    """
    # 加入对话历史
    conversation_history.append({"role": "user", "content": user_text})
    
    # 限制历史长度（保留 system prompt）
    _trim_history(conversation_history)
    
    # 选择 LLM 服务
    if provider == "ollama":
        llm_stream = ollama_llm.chat_stream(conversation_history, model=model)
    else:
        llm_stream = qwen_llm.chat_stream(conversation_history, model=model)
    
    # 收集完整回复
    full_response = ""
    
    # 文本分片缓冲
    text_buffer = ""
    
    # 使用 asyncio.Queue 实现真正的异步音频转发
    audio_queue: asyncio.Queue = asyncio.Queue()
    
    # 创建 TTS 合成器
    from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat, ResultCallback
    
    import dashscope as _dashscope
    _dashscope.api_key = settings.api_key
    
    # === 自定义回调：将音频分片推入 asyncio 队列 ===
    loop = asyncio.get_running_loop()
    
    class RealtimeCallback(ResultCallback):
        """将 TTS 音频分片实时推入 asyncio 队列"""
        def on_open(self):
            logger.debug("TTS stream opened")
        
        def on_data(self, data: bytes):
            if data:
                loop.call_soon_threadsafe(audio_queue.put_nowait, data)
        
        def on_complete(self):
            logger.debug("TTS stream complete")
            loop.call_soon_threadsafe(audio_queue.put_nowait, None)
        
        def on_error(self, message):
            logger.error(f"TTS error: {message}")
            loop.call_soon_threadsafe(audio_queue.put_nowait, None)
        
        def on_close(self):
            pass
        
        def on_event(self, message):
            pass
    
    callback = RealtimeCallback()
    synthesizer = SpeechSynthesizer(
        model=settings.COSYVOICE_MODEL,
        voice=voice or settings.COSYVOICE_DEFAULT_VOICE,
        format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
        callback=callback,
    )
    
    # === 异步任务：实时转发音频分片到 WebSocket ===
    async def forward_audio():
        """从 asyncio 队列取出音频分片，实时发送给前端"""
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            try:
                await websocket.send_bytes(chunk)
            except Exception as e:
                logger.error(f"Error sending audio chunk: {e}")
                break
    
    # 启动音频转发任务
    audio_forward_task = asyncio.create_task(forward_audio())
    
    # === LLM 流式生成 + 文本发送 + TTS 喂文本 ===
    try:
        async for chunk in llm_stream:
            full_response += chunk
            text_buffer += chunk
            
            # 发送 LLM 文本片段给前端（打字机效果）
            await websocket.send_json({
                "type": "llm_chunk",
                "text": chunk,
            })
            
            # 遇到句子边界且积累足够长度时，喂给 TTS
            if len(text_buffer) > 10 and text_buffer.rstrip()[-1:] in ".!?,;:。！？，；：\n":
                await loop.run_in_executor(
                    None, synthesizer.streaming_call, text_buffer
                )
                text_buffer = ""
        
        # 发送剩余文本给 TTS
        if text_buffer.strip():
            await loop.run_in_executor(
                None, synthesizer.streaming_call, text_buffer
            )
        
        # 通知 LLM 文本结束
        await websocket.send_json({"type": "llm_done"})
        
        # 通知 TTS 合成结束（等待音频全部产生）
        await loop.run_in_executor(None, synthesizer.streaming_complete)
        
    except Exception as e:
        logger.error(f"LLM/TTS streaming error: {e}")
        try:
            await loop.run_in_executor(None, synthesizer.streaming_complete)
        except Exception:
            pass
        raise
    finally:
        # 等待音频转发任务完成
        await audio_forward_task
    
    # 记录完整回复到对话历史
    conversation_history.append({"role": "assistant", "content": full_response})
    
    # 发送完成信号
    await websocket.send_json({"type": "complete"})
    
    logger.info(f"Pipeline complete: user='{user_text[:50]}' ai='{full_response[:50]}'")


def _trim_history(history: list[dict]):
    """修剪对话历史，保留 system prompt 和最近 N 轮"""
    if len(history) <= MAX_HISTORY_TURNS * 2 + 1:
        return
    
    # 查找 system prompt
    system_msgs = [m for m in history if m["role"] == "system"]
    non_system = [m for m in history if m["role"] != "system"]
    
    # 保留最近的对话
    keep = non_system[-(MAX_HISTORY_TURNS * 2):]
    
    history.clear()
    history.extend(system_msgs)
    history.extend(keep)