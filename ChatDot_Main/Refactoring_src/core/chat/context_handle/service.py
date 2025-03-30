from typing import List, Dict, Optional, Tuple
from global_managers.service_manager import ServiceManager
from chat.context_handle.providers.base import BaseContextHandler
from chat.context_handle.manager import ContextHandleManager

class ContextHandleService:
    """上下文处理器服务层"""
    
    def __init__(self):
        self.service_manager = ServiceManager()
        self.manager = ContextHandleManager()
        
    def initialize(self):
        """初始化服务"""
        # 如果需要其他服务的依赖，可以在这里获取
        pass

    def get_available_handlers(self) -> List[Dict]:
        """获取所有可用的处理器"""
        return self.manager.get_available_handlers()

    def set_current_handler(self, handler_name: str) -> bool:
        """设置当前处理器"""
        return self.manager.set_handler(handler_name)

    def get_current_handler(self) -> Optional[BaseContextHandler]:
        """获取当前处理器"""
        return self.manager.get_current_handler()

    def process_before_send(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
            """
            处理消息
            
            Args:
                messages: 原始消息列表
                
            Returns:
                Tuple[List[Dict], List[Dict]]: (本地消息列表, 发送给LLM的消息列表)
            """
            return self.manager.process_before_send(messages)