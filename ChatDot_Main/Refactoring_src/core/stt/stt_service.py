"""
STT服务类，集成到服务管理系统
"""
import asyncio
import threading
import time
from typing import Callable, List

from global_managers.logger_manager import LoggerManager
from .settings import STTSettings
from .funasr_client import FunASRClient
from .funasr_server import FunASRServer

class STTService:
    """语音转文本服务"""
    
    def __init__(self):
        self.settings = STTSettings()
        self.server = FunASRServer()
        self.client = None
        self.recognition_thread = None
        self.is_initialized = False
        self.logger = LoggerManager().get_logger()
        self.segment_callbacks: List[Callable[[str], None]] = []
        self.last_text = ""
        self.auto_start_server = True

    def initialize(self) -> bool:
        """初始化STT服务"""
        if self.is_initialized:
            return True
            
        if not self.settings.get_setting("enabled"):
            self.logger.info("STT服务未启用")
            return False
            
        try:
            self.logger.info("初始化STT服务...")
            
            # 配置并启动FunASR服务器
            if self.auto_start_server:
                host = self.settings.get_setting("host")
                port = self.settings.get_setting("port")
                
                # 配置服务器
                self.server.set_config(
                    host=host,
                    port=port,
                    device="cuda"  # 可以从设置中获取
                )
                
                # 启动服务器
                if not self.server.start():
                    self.logger.error("启动FunASR服务器失败")
                    return False
                    
                # 等待服务器初始化
                self.logger.info("等待FunASR服务器初始化...")
                time.sleep(2)
            
            self.is_initialized = True
            self.logger.info("STT服务初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"初始化STT服务失败: {e}")
            return False

    def shutdown(self) -> None:
        """关闭STT服务"""
        if not self.is_initialized:
            return
            
        self.logger.info("关闭STT服务...")
        
        # 停止语音识别
        self.stop_recognition()
        
        # 停止服务器
        if self.auto_start_server and self.server:
            self.server.stop()
        
        self.is_initialized = False
        self.logger.info("STT服务已关闭")

    def set_auto_start_server(self, auto_start: bool) -> None:
        """设置是否自动启动服务器"""
        self.auto_start_server = auto_start

    def add_segment_callback(self, callback: Callable[[str], None]) -> None:
        """
        添加完整语音片段回调函数
        
        Args:
            callback: 回调函数，接收参数(text: str)
        """
        self.segment_callbacks.append(callback)
        
    def _on_segment(self, text: str) -> None:
        """内部回调处理"""
        self.last_text = text
        
        # 触发所有注册的回调
        for callback in self.segment_callbacks:
            try:
                callback(text)
            except Exception as e:
                self.logger.error(f"回调函数执行错误: {e}")

    def start_recognition(self) -> bool:
        """
        启动语音识别 (非阻塞)
        
        Returns:
            bool: 是否成功启动
        """
        if not self.is_initialized:
            if not self.initialize():
                return False
                
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.logger.info("语音识别已在运行")
            return True
            
        # 创建FunASR客户端
        host = self.settings.get_setting("host")
        port = self.settings.get_setting("port")
        use_ssl = self.settings.get_setting("use_ssl")
        
        self.client = FunASRClient(host=host, port=port, use_ssl=use_ssl)
        
        # 设置回调
        self.client.add_segment_callback(self._on_segment)
        
        # 在新线程中启动语音识别
        def run_recognition():
            asyncio.run(self.client.start())
            
        self.recognition_thread = threading.Thread(
            target=run_recognition,
            daemon=True
        )
        self.recognition_thread.start()
        self.logger.info("语音识别已启动")
        return True

    def stop_recognition(self) -> None:
        """停止语音识别"""
        if not self.client:
            return
            
        self.logger.info("停止语音识别...")
        self.client.stop()
        
        # 等待线程结束
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=2)
            
        self.client = None
        self.recognition_thread = None
        self.logger.info("语音识别已停止")

    def is_recognition_active(self) -> bool:
        """检查语音识别是否正在运行"""
        return (self.recognition_thread is not None and 
                self.recognition_thread.is_alive())
                
    def get_last_text(self) -> str:
        """获取最后识别的文本"""
        return self.last_text