from typing import List, Type, Any
from global_managers.service_manager import ServiceManager
from chat.service import ChatService
from chat.context_handle.service import ContextHandleService
from client.llm.service import LLMService

class Bootstrap:
    """
    应用程序引导类
    负责注册和初始化所有服务
    """
    def __init__(self):
        self.service_manager = ServiceManager()
        self._service_registry = []
        self._register_core_services()

    def _register_core_services(self):
        """注册核心服务"""
        # 按依赖顺序注册服务
        self._service_registry.extend([
            ("llm_service", LLMService),             # LLM服务
            ("context_handle_service", ContextHandleService),  # 上下文处理服务
            ("chat_service", ChatService),           # 聊天服务
        ])

    # def register_service(self, service_name: str, service_class: Type[Any]):
    #     """注册额外的服务"""
    #     self._service_registry.append((service_name, service_class))

    def initialize(self):
        """初始化所有服务"""
        # 注册服务
        for service_name, service_class in self._service_registry:
            self.service_manager.register_service(service_name, service_class)

        # 初始化服务
        for service_name, _ in self._service_registry:
            self.service_manager.initialize_service(service_name)

    def shutdown(self):
        """关闭所有服务"""
        # 按注册的相反顺序关闭服务
        for service_name, _ in reversed(self._service_registry):
            self.service_manager.shutdown_service(service_name)