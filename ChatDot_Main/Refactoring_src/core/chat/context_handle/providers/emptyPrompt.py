from chat.context_handle.providers.base import BaseContextHandler
from typing import List, Dict, Tuple

class ContextHandler(BaseContextHandler):
    """示例处理器"""
    
    def __init__(self):
        pass
        
    def process_before_send(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """处理发送前的消息列表"""
        local_messages = messages.copy()
        llm_messages = messages.copy()
        
        return local_messages, llm_messages
        
    def get_prompt_info(self) -> Dict:
        return {
            "name": "空白处理器",
            "description": "一个空白的的消息处理器示例",
            "version": "1.0"
        }