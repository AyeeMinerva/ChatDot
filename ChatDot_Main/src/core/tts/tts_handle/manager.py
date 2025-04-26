import os
import importlib.util
from typing import Dict, Optional, List, Type
from tts.tts_handle.base import BaseTTSHandler
from tts.tts_handle.settings import TTSHandleSettings
from tts.tts_handle.persistence import TTSHandlePersistence
from global_managers.logger_manager import LoggerManager

class TTSHandleManager:
    """TTS处理器管理器，负责加载、管理和切换TTS处理器"""
    
    def __init__(self):
        self.settings = TTSHandleSettings()
        self.persistence = TTSHandlePersistence()
        self.handlers: Dict[str, Type[BaseTTSHandler]] = {}
        self.current_handler: Optional[BaseTTSHandler] = None
        self.handlers_dir = os.path.join(os.path.dirname(__file__), "providers")
        
        # 初始化
        self.load_handlers()
        self.initialize_default_handler()

    def load_handlers(self) -> None:
        """加载所有可用的TTS处理器"""
        if not os.path.exists(self.handlers_dir):
            os.makedirs(self.handlers_dir, exist_ok=True)
            LoggerManager().get_logger().warning(f"TTS处理器目录不存在，已创建: {self.handlers_dir}")
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
                    LoggerManager().get_logger().warning(f"加载TTS处理器 {handler_name} 失败: {str(e)}")

    def initialize_default_handler(self) -> None:
        """初始化默认处理器"""
        # 尝试加载上次使用的处理器
        last_handler = self.persistence.load_current_handler()
        if not self.set_handler(last_handler):
            # 如果失败，使用默认处理器
            if 'sentence' in self.handlers:
                self.set_handler('sentence')
            else:
                LoggerManager().get_logger().warning("警告: 无法加载默认TTS处理器")

    def set_handler(self, handler_name: str) -> bool:
        """设置当前使用的处理器"""
        if handler_name not in self.handlers:
            return False
            
        try:
            self.current_handler = self.handlers[handler_name]()
            self.persistence.save_current_handler(handler_name)
            return True
        except Exception as e:
            LoggerManager().get_logger().warning(f"设置TTS处理器 {handler_name} 失败: {str(e)}")
            return False

    def get_current_handler(self) -> Optional[BaseTTSHandler]:
        """获取当前使用的处理器"""
        return self.current_handler

    def get_available_handlers(self) -> List[Dict]:
        """获取所有可用的处理器信息"""
        handlers_info = []
        for name, handler_class in self.handlers.items():
            try:
                handler = handler_class()
                info = handler.get_handler_info()
                info['id'] = name
                handlers_info.append(info)
            except Exception as e:
                LoggerManager().get_logger().warning(f"获取TTS处理器 {name} 信息失败: {str(e)}")
        return handlers_info