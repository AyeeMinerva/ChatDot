import re
from chat.context_handle.providers.base import BaseContextHandler
from typing import List, Dict, Tuple

class ContextHandler(BaseContextHandler):
    """示例处理器"""
    
    def __init__(self):
        self.system_prompt = "你是一个专业的AI助手。将你的思考过程包含在<thinking></thinking>标签中。"
        self.thinking_pattern = re.compile(r'<thinking>.*?</thinking>', re.DOTALL)
        
    def process_before_send(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """处理发送前的消息列表"""
        local_messages = messages.copy()
        llm_messages = []
        
        llm_messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # 添加其他消息
        llm_messages.extend(messages)
        
        return local_messages, llm_messages
    
    def process_before_show(self, text: str) -> str:
        """处理完整的回复文本，移除thinking标签及其内容"""
        return self.thinking_pattern.sub('', text)
        
    def get_prompt_info(self) -> Dict:
        return {
            "name": "基础处理器",
            "description": "一个简单的消息处理器示例",
            "version": "1.0"
        }