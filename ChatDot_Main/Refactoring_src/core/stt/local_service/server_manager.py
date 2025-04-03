"""
FunASR服务器管理器
负责启动和管理本地FunASR服务器
"""
import threading
import time
from typing import Dict, Any
from global_managers.logger_manager import LoggerManager
from .funasr_server import FunASRServer

class ServerManager:
    """FunASR服务器管理器"""
    
    def __init__(self):
        """初始化服务器管理器"""
        self.server = FunASRServer()
        self.logger = LoggerManager().get_logger()
        
    def set_config(self, host: str = "localhost", port: int = 10095, 
                  device: str = "cuda", ngpu: int = 1, ncpu: int = 4,
                  models: Dict[str, str] = None) -> None:
        """
        设置服务器配置
        
        Args:
            host: 服务器地址
            port: 服务器端口
            device: 设备类型 (cuda/cpu)
            ngpu: GPU数量
            ncpu: CPU核心数
            models: 模型配置
        """
        self.server.set_config(
            host=host,
            port=port,
            device=device,
            ngpu=ngpu,
            ncpu=ncpu,
            models=models
        )
        
    def start(self) -> bool:
        """
        启动服务器
        
        Returns:
            bool: 是否成功启动
        """
        try:
            self.logger.info("启动本地FunASR服务器...")
            return self.server.start()
        except Exception as e:
            self.logger.error(f"启动FunASR服务器失败: {e}")
            return False
            
    def stop(self) -> None:
        """停止服务器"""
        try:
            self.logger.info("停止本地FunASR服务器...")
            self.server.stop()
            self.logger.info("服务器已停止")
        except Exception as e:
            self.logger.error(f"停止FunASR服务器失败: {e}")
            
    def is_running(self) -> bool:
        """
        检查服务器是否在运行
        
        Returns:
            bool: 服务器是否在运行
        """
        return self.server.is_running