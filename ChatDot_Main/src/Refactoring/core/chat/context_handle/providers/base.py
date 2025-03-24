from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

class BaseContextHandler(ABC):
    """聊天处理的抽象基类"""
    
    @abstractmethod
    def process_before_send(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        处理发送前的消息列表
        
        Args:
            messages: 原始消息列表
            
        Returns:
            tuple: (local_messages, llm_messages)
            - local_messages: 保存在本地的消息列表
            - llm_messages: 发送给LLM的消息列表
        """
        pass
        
    @abstractmethod
    def get_prompt_info(self) -> Dict:
        """获取当前prompt的信息"""
        pass