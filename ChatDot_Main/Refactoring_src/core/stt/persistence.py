"""
STT模块的持久化管理
"""
import os
import json
from typing import Dict, Any, Optional
from global_managers.persistence_manager import PersistenceManager
from global_managers.logger_manager import LoggerManager

class STTPersistence:
    """STT持久化管理类"""
    
    def __init__(self):
        """初始化持久化管理器"""
        self.persistence_manager = PersistenceManager()
        self.logger = LoggerManager().get_logger()
        
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置到持久化存储
        
        Args:
            config: 要保存的配置
            
        Returns:
            bool: 保存是否成功
        """
        try:
            self.persistence_manager.save("stt", config)
            return True
        except Exception as e:
            self.logger.error(f"保存STT配置失败: {e}")
            return False
            
    def load_config(self) -> Dict[str, Any]:
        """
        从持久化存储加载配置
        
        Returns:
            Dict[str, Any]: 加载的配置
        """
        try:
            return self.persistence_manager.load("stt")
        except Exception as e:
            self.logger.error(f"加载STT配置失败: {e}")
            return {}
            
    def save_server_state(self, state: Dict[str, Any]) -> bool:
        """
        保存服务器状态
        
        Args:
            state: 服务器状态信息
            
        Returns:
            bool: 保存是否成功
        """
        try:
            self.persistence_manager.save("stt_server", state)
            return True
        except Exception as e:
            self.logger.error(f"保存STT服务器状态失败: {e}")
            return False
            
    def load_server_state(self) -> Dict[str, Any]:
        """
        加载服务器状态
        
        Returns:
            Dict[str, Any]: 服务器状态信息
        """
        try:
            return self.persistence_manager.load("stt_server")
        except Exception as e:
            self.logger.error(f"加载STT服务器状态失败: {e}")
            return {}