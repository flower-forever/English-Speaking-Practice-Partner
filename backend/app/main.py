from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, stt, tts, voice, websocket, scenes
from app.core.config import settings

app = FastAPI(
    title="NAGA - AI 英语口语陪练",
    description="本地 AI 英语口语陪练助手 API",
    version="0.1.0"
)

# 配置 CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(stt.router, prefix="/api/stt", tags=["语音识别"])
app.include_router(tts.router, prefix="/api/tts", tags=["语音合成"])
app.include_router(voice.router, prefix="/api/voice", tags=["音色克隆"])
app.include_router(websocket.router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(scenes.router, prefix="/api/scenes", tags=["情景模拟"])

@app.get("/")
async def root():
    return {"message": "NAGA API 运行中", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)