from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.services.voice_db import voice_db

router = APIRouter()

# 音频文件存储目录
AUDIO_DIR = "data/voices"
os.makedirs(AUDIO_DIR, exist_ok=True)

class VoiceRole(BaseModel):
    id: str
    name: str
    voice_id: str
    source_audio: Optional[str] = None
    created_at: str
    language: Optional[str] = "en-US"

@router.post("/clone")
async def clone_voice(
    file: UploadFile = File(...),
    name: str = Form(...)
):
    """
    克隆音色 - 上传音频并创建角色
    """
    # 1. 验证文件格式
    allowed_extensions = [".mp3", ".wav", ".flac"]
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，仅支持：{', '.join(allowed_extensions)}"
        )
    
    # 2. 生成唯一 ID 和保存路径
    role_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{role_id}_{timestamp}{file_ext}"
    file_path = os.path.join(AUDIO_DIR, safe_filename)
    
    # 3. 保存音频文件
    try:
        content = await file.read()
        
        # 检查文件大小 (< 10MB)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败：{str(e)}")
    
    # 4. 调用阿里云声音复刻 API
    try:
        from app.services.aliyun_voice_clone import aliyun_voice_clone
        voice_id = await aliyun_voice_clone.clone(file_path, name)
    except Exception as e:
        # 删除已保存的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"声音复刻失败：{str(e)}")
    
    # 5. 保存角色信息
    role = {
        "id": role_id,
        "name": name,
        "voice_id": voice_id,
        "source_audio": safe_filename,
        "created_at": datetime.now().isoformat(),
        "language": "en-US"
    }
    voice_db.add(role_id, role)
    
    return {
        "id": role_id,
        "name": name,
        "voice_id": voice_id,
        "message": "音色克隆成功"
    }

@router.get("/roles")
async def list_roles():
    """获取所有角色列表"""
    return {"roles": voice_db.list_all()}

@router.get("/roles/{role_id}")
async def get_role(role_id: str):
    """获取单个角色详情"""
    role = voice_db.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role

@router.delete("/roles/{role_id}")
async def delete_role(role_id: str):
    """删除角色"""
    role = voice_db.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 删除音频文件
    if role.get("source_audio"):
        file_path = os.path.join(AUDIO_DIR, role["source_audio"])
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # 删除角色信息
    voice_db.delete(role_id)
    
    return {"success": True, "message": "角色已删除"}

@router.post("/roles/{role_id}/test")
async def test_voice(role_id: str, text: str = Form(...)):
    """测试音色 - 用指定音色合成一段语音"""
    role = voice_db.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    from app.services.cosyvoice_tts import cosyvoice_tts
    
    # 使用角色音色合成语音
    audio_data = await cosyvoice_tts.synthesize(text, voice=role["voice_id"])
    
    from fastapi import Response
    return Response(content=audio_data, media_type="audio/mp3")