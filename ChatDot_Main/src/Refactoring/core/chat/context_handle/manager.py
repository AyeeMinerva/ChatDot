import os
import importlib.util
from typing import Dict, Optional, List, Type
from core.chat.context_handle.providers.base import BaseContextHandler
from core.global_managers.settings_manager import SettingsManager

class ContextHandleManager:
    """
    上下文处理器管理器，负责加载、管理和切换上下文处理器。
    """
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.handlers: Dict[str, Type[BaseContextHandler]] = {}
        self.current_handler: Optional[BaseContextHandler] = None
        self.handlers_dir = os.path.join(
            os.path.dirname(__file__), 
            "providers"
        )
        
        # 初始化
        self.load_handlers()
        self.initialize_default_handler()

    def load_handlers(self) -> None:
        """
        加载所有可用的上下文处理器
        """
        if not os.path.exists(self.handlers_dir):
            return

        for file in os.listdir(self.handlers_dir):
            if file.endswith('.py') and not file.startswith('__'):
                try:
                    # 导入处理器模块
                    module_path = os.path.join(self.handlers_dir, file)
                    module_name = file[:-3]  # 移除 .py 后缀
                    
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 获取处理器类
                    if hasattr(module, 'ContextHandler'):
                        self.handlers[module_name] = getattr(module, 'ContextHandler')
                except Exception as e:
                    print(f"加载处理器 {file} 失败: {str(e)}")

    def initialize_default_handler(self) -> None:
        """
        初始化默认处理器
        """
        if 'defaultPrompt' in self.handlers:
            self.set_handler('defaultPrompt')
        else:
            print("警告: 默认处理器未找到")

    def set_handler(self, handler_name: str) -> bool:
        """
        设置当前使用的处理器
        
        Args:
            handler_name: 处理器名称
            
        Returns:
            bool: 是否成功设置处理器
        """
        if handler_name not in self.handlers:
            return False
            
        try:
            self.current_handler = self.handlers[handler_name]()
            # 保存当前处理器设置
            self.settings_manager.update_setting("chat", "current_handler", handler_name)
            return True
        except Exception as e:
            print(f"设置处理器 {handler_name} 失败: {str(e)}")
            return False

    def get_current_handler(self) -> Optional[BaseContextHandler]:
        """
        获取当前使用的处理器
        
        Returns:
            Optional[BaseContextHandler]: 当前处理器实例，如果未设置则返回 None
        """
        return self.current_handler

    def get_available_handlers(self) -> List[Dict]:
        """
        获取所有可用的处理器信息
        
        Returns:
            List[Dict]: 处理器信息列表，每个字典包含处理器的名称和描述信息
        """
        handlers_info = []
        for name, handler_class in self.handlers.items():
            try:
                handler = handler_class()
                info = handler.get_prompt_info()
                info['id'] = name
                handlers_info.append(info)
            except Exception as e:
                print(f"获取处理器 {name} 信息失败: {str(e)}")
        return handlers_info

    def process_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        使用当前处理器处理消息
        
        Args:
            messages: 要处理的消息列表
            
        Returns:
            List[Dict]: 处理后的消息列表
        """
        if not self.current_handler:
            return messages
            
        try:
            local_messages, llm_messages = self.current_handler.process_before_send(messages)
            return llm_messages
        except Exception as e:
            print(f"处理消息失败: {str(e)}")
            return messages