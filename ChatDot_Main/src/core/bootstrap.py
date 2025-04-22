from typing import List, Type, Any
from global_managers.service_manager import ServiceManager
from chat.service import ChatService
from chat.context_handle.service import ContextHandleService
from client.llm.service import LLMService
from live2d.service import Live2DService
from global_managers.logger_manager import LoggerManager
from tts.service import TTSService
from stt.service import STTService
from rag.rag_service import RAGService

class Bootstrap:
    """
    应用程序引导类 (单例模式)
    负责注册和初始化所有服务
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Bootstrap, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance._services_registered = False
            cls._instance._services_initialized = False
            cls._instance._service_registry = []
            cls._instance.service_manager = ServiceManager()
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._register_core_services()
            self._initialized = True

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            return cls()
        return cls._instance

    def _register_core_services(self):
        """注册核心服务 (只能调用一次)"""
        if self._services_registered:
            print("Bootstrap: _register_core_services 服务已注册，无需重复注册")
            return
            
        # 按依赖顺序注册服务
        self._service_registry.extend([
            ("live2d_service", Live2DService),       # Live2D服务
            ("tts_service", TTSService),             # TTS服务
            ("stt_service", STTService),             # STT服务
            
            ("llm_service", LLMService),             # LLM服务
            ("context_handle_service", ContextHandleService),  # 上下文处理服务
            ("rag_service", RAGService),             # RAG服务
            ("chat_service", ChatService),           # 聊天服务
        ])
        
        self._services_registered = True

    # def register_service(self, service_name: str, service_class: Type[Any]):
    #     """注册额外的服务"""
    #     self._service_registry.append((service_name, service_class))

    def initialize(self):
        """初始化所有服务 (只能调用一次)"""
        if self._services_initialized:
            print("Bootstrap: initialize 服务已初始化，无需重复初始化")
            return
            
        # 注册服务
        for service_name, service_class in self._service_registry:
            self.service_manager.register_service(service_name, service_class)

        # 初始化服务
        for service_name, _ in self._service_registry:
            self.service_manager.initialize_service(service_name)
            
        self._services_initialized = True

    def shutdown(self):
        """关闭所有服务"""
        # 按注册的相反顺序关闭服务
        for service_name, _ in reversed(self._service_registry):
            self.service_manager.shutdown_service(service_name)
        
        # 重置初始化状态，允许重新初始化
        self._services_initialized = False