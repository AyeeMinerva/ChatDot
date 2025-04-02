import os
import importlib.util
from typing import Dict, Optional, List, Type
from chat.context_handle.providers.base import BaseContextHandler
from chat.context_handle.settngs import ContextHandleSettings
from chat.context_handle.persistence import ContextHandlePersistence
from global_managers.logger_manager import LoggerManager

class ContextHandleManager:
    """上下文处理器管理器，负责加载、管理和切换上下文处理器"""
    
    def __init__(self):
        self.settings = ContextHandleSettings()
        self.persistence = ContextHandlePersistence()
        self.handlers: Dict[str, Type[BaseContextHandler]] = {}
        self.current_handler: Optional[BaseContextHandler] = None
        self.handlers_dir = os.path.join(os.path.dirname(__file__), "providers")
        
        # 初始化
        self.load_handlers()
        self.initialize_default_handler()

    def load_handlers(self) -> None:
        """加载所有可用的上下文处理器"""
        if not os.path.exists(self.handlers_dir):
            return

        for file in os.listdir(self.handlers_dir):
            if file.endswith('.py') and not file.startswith('__'):
                handler_name = file[:-3]
                try:
                    # 动态加载模块
                    spec = importlib.util.spec_from_file_location(
                        handler_name,
                        os.path.join(self.handlers_dir, file)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 注册处理器
                    if hasattr(module, 'ContextHandler'):
                        self.handlers[handler_name] = module.ContextHandler
                except Exception as e:
                    LoggerManager().get_logger().warning(f"加载处理器 {handler_name} 失败: {str(e)}")

    def initialize_default_handler(self) -> None:
        """初始化默认处理器"""
        # 尝试加载上次使用的处理器
        last_handler = self.persistence.load_current_handler()
        if not self.set_handler(last_handler):
            # 如果失败，使用默认处理器
            if 'defaultPrompt' in self.handlers:
                self.set_handler('defaultPrompt')
            else:
                LoggerManager().get_logger().warning("警告: 无法加载默认处理器")

    def set_handler(self, handler_name: str) -> bool:
        """设置当前使用的处理器"""
        if handler_name not in self.handlers:
            return False
            
        try:
            self.current_handler = self.handlers[handler_name]()
            self.persistence.save_current_handler(handler_name)
            return True
        except Exception as e:
            LoggerManager().get_logger().warning(f"设置处理器 {handler_name} 失败: {str(e)}")
            return False

    def get_current_handler(self) -> Optional[BaseContextHandler]:
        """获取当前使用的处理器"""
        return self.current_handler

    def get_available_handlers(self) -> List[Dict]:
        """获取所有可用的处理器信息"""
        handlers_info = []
        for name, handler_class in self.handlers.items():
            try:
                handler = handler_class()
                info = handler.get_prompt_info()
                info['id'] = name
                handlers_info.append(info)
            except Exception as e:
                LoggerManager().get_logger().warning(f"获取处理器 {name} 信息失败: {str(e)}")
        return handlers_info

    # def process_before_send(self, messages: List[Dict]) -> List[Dict]:
    #     """处理消息列表"""
    #     if not self.current_handler:
    #         raise RuntimeError("未设置当前处理器")
    #     local_messages, llm_messages = self.current_handler.process_before_send(messages)
    #     return local_messages,llm_messages
    
    # def process_before_show(self, text: str) -> str:
    #     """处理显示前的完整文本"""
    #     if not self.current_handler:
    #         return text
    #     return self.current_handler.process_before_show(text)