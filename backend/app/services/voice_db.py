import json
import os
from typing import Dict, List, Optional

DATA_FILE = "data/voice_roles.json"

class VoiceDatabase:
    """角色数据库 - 简单的 JSON 文件存储"""
    
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.roles = self._load()
    
    def _load(self) -> Dict:
        """从文件加载数据"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save(self):
        """保存数据到文件"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.roles, f, ensure_ascii=False, indent=2)
    
    def add(self, role_id: str, role_data: dict):
        """添加角色"""
        self.roles[role_id] = role_data
        self._save()
    
    def get(self, role_id: str) -> Optional[dict]:
        """获取角色"""
        return self.roles.get(role_id)
    
    def list_all(self) -> List[dict]:
        """列出所有角色"""
        return list(self.roles.values())
    
    def delete(self, role_id: str) -> bool:
        """删除角色"""
        if role_id in self.roles:
            del self.roles[role_id]
            self._save()
            return True
        return False

# 全局实例
voice_db = VoiceDatabase()