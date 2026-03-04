from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json

router = APIRouter()

# 场景数据目录
SCENES_DIR = "data/scenes"
os.makedirs(SCENES_DIR, exist_ok=True)

def _load_scene(scene_id: str) -> Optional[dict]:
    """加载场景文件"""
    # 按分类查找
    for category in ["work", "study"]:
        file_path = os.path.join(SCENES_DIR, category, f"{scene_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None

def _list_all_scenes() -> List[dict]:
    """列出所有场景"""
    scenes = []
    for category in ["work", "study"]:
        category_dir = os.path.join(SCENES_DIR, category)
        if not os.path.exists(category_dir):
            continue
        for filename in os.listdir(category_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(category_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    scene = json.load(f)
                    scenes.append(scene)
    return scenes

@router.get("/categories")
async def list_categories():
    """获取分类列表"""
    return {
        "categories": [
            {"id": "work", "name": "工作场景", "nameEn": "Work", "count": 4},
            {"id": "study", "name": "学习场景", "nameEn": "Study", "count": 4}
        ]
    }

@router.get("/tags")
async def list_tags():
    """获取热门标签"""
    all_scenes = _list_all_scenes()
    tags = []
    for scene in all_scenes:
        tags.extend(scene.get("tags", []))

    # 去重并统计
    from collections import Counter
    tag_counts = Counter(tags)

    return {
        "tags": [
            {"name": tag, "count": count}
            for tag, count in tag_counts.most_common(10)
        ]
    }

@router.get("/")
async def list_scenes(category: Optional[str] = None):
    """
    获取场景列表

    Args:
        category: 分类过滤 (work/study)
    """
    all_scenes = _list_all_scenes()

    if category:
        all_scenes = [s for s in all_scenes if s.get("category") == category]

    # 只返回基本信息
    return {
        "scenes": [
            {
                "id": s["id"],
                "name": s["name"],
                "nameEn": s["nameEn"],
                "category": s["category"],
                "difficulty": s["difficulty"],
                "description": s["description"],
                "estimatedDuration": s["estimatedDuration"],
                "tags": s["tags"]
            }
            for s in all_scenes
        ]
    }

@router.get("/{scene_id}")
async def get_scene(scene_id: str):
    """获取场景详情"""
    scene = _load_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scene