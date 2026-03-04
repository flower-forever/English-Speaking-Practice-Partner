from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.whisper_stt import whisper_stt

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    语音转文字（使用 faster-whisper 本地识别）
    """
    try:
        audio_data = await file.read()
        text = await whisper_stt.transcribe(audio_data)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))