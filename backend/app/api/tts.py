from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
from app.services.cosyvoice_tts import cosyvoice_tts, COSYVOICE_VOICES

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = ""
    format: Optional[str] = "mp3"

@router.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    文字转语音（使用 CosyVoice v3）
    """
    try:
        audio_data = await cosyvoice_tts.synthesize(
            text=request.text,
            voice=request.voice or "",
        )
        return Response(content=audio_data, media_type="audio/mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices")
async def list_voices():
    """获取可用音色列表"""
    return {"voices": COSYVOICE_VOICES}