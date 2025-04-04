from typing import Iterator, List, Dict, Optional, Callable, Tuple
from global_managers.service_manager import ServiceManager
from global_managers.logger_manager import LoggerManager
from chat.client import ChatClient
from chat.settings import ChatSettings
from chat.persistence import ChatPersistence

class ChatService:
    def __init__(self):
        self.service_manager = ServiceManager()
        self.settings = ChatSettings()
        self.persistence = ChatPersistence()
        self.client = None
        # 添加生成状态跟踪属性
        self.is_generating = False

    def initialize(self):
        """初始化服务"""
        # 获取依赖的服务
        llm_service = self.service_manager.get_service("llm_service")
        
        # 初始化客户端
        self.client = ChatClient(llm_service, self.service_manager, self.persistence)
        self.client.initialize()
        
        # 加载历史记录
        history = self.persistence.load_history()
        self.client.set_messages(history)

    def send_message(self, message: str, is_stream: bool = True) -> Iterator[str]:
        """
        发送消息并返回响应迭代器
        
        Args:
            message: 用户输入的消息
            is_stream: 是否使用流式输出
            
        Returns:
            Iterator[str]: 响应迭代器
        """
        # 设置生成状态为True
        self.is_generating = True
        
        local_messages, response_iter = self.client.send_message(message, is_stream)
        
        # 包装响应迭代器以在完成时更新状态
        def wrapped_iterator():
            try:
                for chunk in response_iter:
                    yield chunk
            finally:
                self.is_generating = False
        
        # 返回包装后的迭代器
        return wrapped_iterator()
    
    def stop_generating(self):
        """停止当前生成过程"""
        if self.client:
            self.client.stop_generating()
            # 更新生成状态
            self.is_generating = False

    def clear_context(self):
        """清空上下文"""
        self.client.clear_context()
        self.persistence.save_history([])

    def get_messages(self) -> List[Dict]:
        """获取所有消息"""
        return self.client.get_messages()

    def export_history(self, filepath: str = None):
        """导出历史记录"""
        messages = self.client.get_messages()
        return self.persistence.export_history(filepath, messages)

    def import_history(self, filepath: str):
        """导入历史记录"""
        messages = self.persistence.import_history(filepath)
        self.client.set_messages(messages)
        self.persistence.save_history(messages)