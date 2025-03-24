from typing import List, Dict, Optional, Callable, Tuple
from core.chat.client import ChatClient
from core.chat.persistence import ChatPersistence
from core.chat.settings import ChatSettings
from core.client.llm.service import LLMService

class ChatService:
    def __init__(self):
        self.client = ChatClient()
        self.persistence = ChatPersistence()
        self.settings = ChatSettings()
        self.llm_service = LLMService()

    def initialize(self):
        """初始化服务"""
        self.llm_service.initialize()
        self.load_history()

    def send_message(self, message: str) -> Tuple[List[Dict], List[Dict]]:
        """同步发送消息"""
        return self.client.send_message(message)

    def send_message_async(self, message: str, 
                          on_response: Optional[Callable[[str], None]] = None,
                          on_error: Optional[Callable[[str], None]] = None):
        """异步发送消息"""
        local_messages, llm_messages = self.client.send_message(message)
        
        def handle_response(response: str):
            self.client.add_response(response)
            if on_response:
                on_response(response)

        self.llm_service.send_message_async(
            llm_messages,
            on_complete=handle_response,
            on_error=on_error
        )

    # 上下文管理
    def clear_context(self):
        """清除上下文"""
        self.client.clear_context()

    def edit_message(self, index: int, new_content: str):
        """编辑消息"""
        self.client.edit_message(index, new_content)

    def delete_message(self, index: int):
        """删除消息"""
        self.client.delete_message(index)

    # 历史记录管理
    def load_history(self):
        """加载当前历史记录"""
        history = self.persistence.load_history()
        self.client.set_messages(history)

    def save_history(self):
        """保存当前历史记录"""
        self.persistence.save_history(self.client.get_messages())

    def export_history(self, filepath: str):
        """导出历史记录到文件"""
        self.persistence.export_history(filepath, self.client.get_messages())

    def import_history(self, filepath: str):
        """从文件导入历史记录"""
        history = self.persistence.import_history(filepath)
        self.client.set_messages(history)

    def get_history_list(self) -> List[Dict]:
        """获取历史记录文件列表"""
        return self.persistence.get_history_list()

    def get_messages(self) -> List[Dict]:
        """获取当前所有消息"""
        return self.client.get_messages()