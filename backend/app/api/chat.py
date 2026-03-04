from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.qwen_llm import qwen_llm, QWEN_MODELS
from app.services.ollama_llm import ollama_llm
from app.api.scenes import _load_scene
from app.core.config import settings

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = ""
    provider: Optional[str] = "aliyun" # aliyun or ollama

class ChatResponse(BaseModel):
    content: str
    model: str
    provider: str

class SceneChatRequest(BaseModel):
    scene_id: str
    message: str
    history: List[Message] = []
    model: Optional[str] = ""
    provider: Optional[str] = "aliyun"

class SceneChatResponse(BaseModel):
    content: str
    scene_id: str
    ai_role: str
    model: str
    provider: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # 转换消息格式
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        if request.provider == "ollama":
            # 调用本地 Ollama API
            response = await ollama_llm.chat(messages, request.model)
        else:
            # 调用 Qwen API
            response = await qwen_llm.chat(messages, request.model)
        
        return ChatResponse(
            content=response,
            model=request.model,
            provider=request.provider
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scene", response_model=SceneChatResponse)
async def scene_chat(request: SceneChatRequest):
    """
    场景模式对话
    
    AI 会根据场景设定调整回复风格和内容
    """
    from app.services.scene_context import SceneContextService
    
    # 加载场景
    scene = _load_scene(request.scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 获取场景上下文服务
    scene_service = SceneContextService(scene)
    
    # 构建带场景上下文的对话
    system_prompt = scene_service.get_system_prompt()
    
    messages = [
        {"role": "system", "content": system_prompt}
    ] + [
        {"role": m.role, "content": m.content} 
        for m in request.history
    ] + [
        {"role": "user", "content": request.message}
    ]
    
    try:
        if request.provider == "ollama":
            response = await ollama_llm.chat(messages, model=request.model)
        else:
            response = await qwen_llm.chat(messages, model=request.model)
            
        return SceneChatResponse(
            content=response,
            scene_id=request.scene_id,
            ai_role=scene["aiRole"]["name"],
            model=request.model,
            provider=request.provider
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """获取所有可用模型（包括云端和本地）"""
    try:
        ollama_models = await ollama_llm.list_models()
    except Exception:
        ollama_models = []
        
    return {
        "providers": {
            "aliyun": QWEN_MODELS,
            "ollama": ollama_models
        }
    }