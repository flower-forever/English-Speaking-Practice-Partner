from typing import Dict, List

class SceneContextService:
    """场景上下文服务 - 为 AI 提供场景相关的系统提示"""
    
    def __init__(self, scene: dict):
        self.scene = scene
    
    def get_system_prompt(self) -> str:
        """
        生成系统提示词
        
        告诉 AI 它当前的角色和对话背景
        """
        ai_role = self.scene["aiRole"]
        background = self.scene["background"]
        
        prompt = f"""You are role-playing as {ai_role['name']} ({ai_role.get('nameEn', '')}).

Context:
{background}

Your role description: {ai_role.get('description', '')}

Instructions:
1. Stay in character as {ai_role['name']} throughout the conversation
2. Speak in English (this is an English speaking practice app)
3. Keep responses concise and natural (1-3 sentences)
4. Ask follow-up questions to keep the conversation going
5. Be encouraging and supportive to the learner
6. If the user struggles, provide hints or simpler questions

Opening line: {ai_role.get('openingLine', 'Hello!')}

Remember: This is a language learning scenario. Be patient and help the user practice English."""

        return prompt
    
    def get_hints(self) -> List[str]:
        """获取提示内容"""
        return self.scene.get("usefulExpressions", [])
    
    def get_topics(self) -> List[str]:
        """获取建议话题"""
        return self.scene.get("suggestedTopics", [])