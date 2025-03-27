from typing import Dict, Type, Any

class ServiceManager:
    """
    服务管理器
    负责管理应用中所有服务的生命周期，提供服务注册、获取和状态管理功能
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(ServiceManager, cls).__new__(cls)
            cls._instance._services = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register_service(self, service_name: str, service_class: Type[Any]) -> None:
        """
        注册一个服务
        
        Args:
            service_name: 服务名称
            service_class: 服务类
        """
        if service_name not in self._services:
            self._services[service_name] = service_class()
    
    def get_service(self, service_name: str) -> Any:
        """
        获取服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            KeyError: 如果请求的服务未注册
        """
        if service_name not in self._services:
            raise KeyError(f"服务 '{service_name}' 未注册")
        return self._services[service_name]
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        获取所有注册的服务
        
        Returns:
            包含所有服务的字典 {服务名: 服务实例}
        """
        return self._services
    
    def initialize_service(self, service_name: str) -> None:
        """
        初始化指定服务
        
        Args:
            service_name: 要初始化的服务名称
            
        Raises:
            KeyError: 如果服务未注册
            RuntimeError: 如果服务初始化失败
        """
        service = self.get_service(service_name)
        if hasattr(service, 'initialize'):
            try:
                service.initialize()
            except Exception as e:
                raise RuntimeError(f"初始化服务 '{service_name}' 失败: {str(e)}")
    
    def shutdown_service(self, service_name: str) -> None:
        """
        关闭指定服务
        
        Args:
            service_name: 要关闭的服务名称
        """
        service = self.get_service(service_name)
        if hasattr(service, 'shutdown'):
            service.shutdown()
    
    def is_service_registered(self, service_name: str) -> bool:
        """
        检查服务是否已注册
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 服务是否已注册
        """
        return service_name in self._services