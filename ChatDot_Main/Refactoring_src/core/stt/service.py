"""
STT服务类，提供语音识别功能
"""
import asyncio
import threading
import time
from typing import Callable, List, Dict, Any, Optional, Union

from global_managers.logger_manager import LoggerManager
from .settings import STTSettings
from .persistence import STTPersistence
from .client import STTClient

# 导入本地服务器管理
try:
    from .local_service import ServerManager
    LOCAL_SERVER_AVAILABLE = True
except ImportError:
    LOCAL_SERVER_AVAILABLE = False

class STTService:
    """语音转文本服务，提供语音识别功能"""
    
    def __init__(self):
        """初始化STT服务"""
        self.settings = STTSettings()
        self.persistence = STTPersistence()
        self.client = STTClient()
        self.server_manager = None
        self.recognition_thread = None
        self.is_initialized = False
        self.logger = LoggerManager().get_logger()
        self.segment_callbacks: List[Callable[[str], None]] = []
        self.last_text = ""
        
        # 从持久化存储加载设置
        self._load_persisted_settings()

    def _load_persisted_settings(self) -> None:
        """从持久化存储加载设置"""
        config = self.persistence.load_config()
        for key, value in config.items():
            self.settings.update_setting(key, value)

    def save_config(self) -> None:
        """保存当前配置到持久化存储"""
        config = {
            # 基本设置
            "enabled": self.settings.get_setting("enabled"),
            "host": self.settings.get_setting("host"),
            "port": self.settings.get_setting("port"),
            "use_ssl": self.settings.get_setting("use_ssl"),
            
            # 服务器设置
            "use_local_server": self.settings.get_setting("use_local_server"),
            "auto_start_server": self.settings.get_setting("auto_start_server"),
            
            # 服务器配置
            "server_config": self.settings.get_setting("server_config")
        }
        self.persistence.save_config(config)

    def initialize(self) -> bool:
        """
        初始化STT服务
        
        Returns:
            bool: 是否成功初始化
        """
        if self.is_initialized:
            return True
            
        if not self.settings.get_setting("enabled"):
            self.logger.info("STT服务未启用")
            return False
            
        try:
            self.logger.info("初始化STT服务...")
            
            # 初始化本地服务器（如果配置为使用本地服务器）
            use_local_server = self.settings.get_setting("use_local_server")
            
            if use_local_server:
                if not LOCAL_SERVER_AVAILABLE:
                    self.logger.warning("未找到本地服务器模块，将使用远程服务器")
                else:
                    auto_start = self.settings.get_setting("auto_start_server")
                    
                    if auto_start:
                        # 创建服务器管理器
                        self.server_manager = ServerManager()
                        
                        # 配置服务器
                        host = self.settings.get_setting("host")
                        port = self.settings.get_setting("port")
                        server_config = self.settings.get_setting("server_config")
                        
                        self.server_manager.set_config(
                            host=host,
                            port=port,
                            **server_config
                        )
                        
                        # 启动服务器
                        if not self.server_manager.start():
                            self.logger.error("启动本地FunASR服务器失败")
                            return False
                            
                        # 等待服务器初始化
                        self.logger.info("等待FunASR服务器初始化...")
                        time.sleep(2)
            
            # 配置客户端
            host = self.settings.get_setting("host")
            port = self.settings.get_setting("port")
            use_ssl = self.settings.get_setting("use_ssl")
            
            self.client.set_server(host, port, use_ssl)
            
            # 设置音频参数
            volume_threshold = self.settings.get_setting("volume_threshold")
            silence_timeout = self.settings.get_setting("silence_timeout")
            self.client.set_audio_params(
                volume_threshold=volume_threshold,
                silence_timeout=silence_timeout
            )
            
            self.is_initialized = True
            self.logger.info("STT服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化STT服务失败: {e}")
            return False
            
    async def initialize_async(self) -> bool:
        """
        异步初始化STT服务
        
        Returns:
            bool: 是否成功初始化
        """
        if self.is_initialized:
            return True
            
        if not self.settings.get_setting("enabled"):
            self.logger.info("STT服务未启用")
            return False
            
        try:
            self.logger.info("初始化STT服务...")
            
            # 初始化本地服务器（如果配置为使用本地服务器）
            use_local_server = self.settings.get_setting("use_local_server")
            
            if use_local_server:
                if not LOCAL_SERVER_AVAILABLE:
                    self.logger.warning("未找到本地服务器模块，将使用远程服务器")
                else:
                    auto_start = self.settings.get_setting("auto_start_server")
                    
                    if auto_start:
                        # 创建服务器管理器
                        self.server_manager = ServerManager()
                        
                        # 配置服务器
                        host = self.settings.get_setting("host")
                        port = self.settings.get_setting("port")
                        server_config = self.settings.get_setting("server_config")
                        
                        self.server_manager.set_config(
                            host=host,
                            port=port,
                            **server_config
                        )
                        
                        # 启动服务器
                        if not self.server_manager.start():
                            self.logger.error("启动本地FunASR服务器失败")
                            return False
                            
                        # 等待服务器初始化
                        self.logger.info("等待FunASR服务器初始化...")
                        await asyncio.sleep(3)
            
            # 配置客户端
            host = self.settings.get_setting("host")
            port = self.settings.get_setting("port")
            use_ssl = self.settings.get_setting("use_ssl")
            
            self.client.set_server(host, port, use_ssl)
            
            self.is_initialized = True
            self.logger.info("STT服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化STT服务失败: {e}")
            return False
        
    def set_audio_threshold(self, threshold: int = None, silence_timeout: float = None) -> None:
        """
        设置音频收录阈值
        
        Args:
            threshold: 音量阈值，0-32767之间的值，越小越灵敏
            silence_timeout: 沉默超时时间(秒)，多久没有声音就中断当前语音片段
        """
        if threshold is not None:
            self.settings.update_setting("volume_threshold", threshold)
            if self.client:
                self.client.set_audio_params(volume_threshold=threshold)
                
        if silence_timeout is not None:
            self.settings.update_setting("silence_timeout", silence_timeout)
            if self.client:
                self.client.set_audio_params(silence_timeout=silence_timeout)
                
        # 保存设置
        self.save_config()
        self.logger.info(f"已更新音频阈值设置: 阈值={threshold}, 超时={silence_timeout}秒")

    def shutdown(self) -> None:
        """关闭STT服务"""
        if not self.is_initialized:
            return
            
        self.logger.info("关闭STT服务...")
        
        # 停止语音识别
        self.stop_recognition()
        
        # 停止本地服务器
        if self.server_manager:
            self.server_manager.stop()
            self.server_manager = None
        
        self.is_initialized = False
        self.logger.info("STT服务已关闭")
        
    async def shutdown_async(self) -> None:
        """异步关闭STT服务"""
        if not self.is_initialized:
            return
            
        self.logger.info("关闭STT服务...")
        
        # 停止语音识别
        await self.stop_recognition_async()
        
        # 停止本地服务器
        if self.server_manager:
            self.server_manager.stop()
            self.server_manager = None
        
        self.is_initialized = False
        self.logger.info("STT服务已关闭")

    def add_segment_callback(self, callback: Callable[[str], None]) -> None:
        """
        添加完整语音片段回调函数
        
        Args:
            callback: 回调函数，接收参数(text: str)
        """
        self.segment_callbacks.append(callback)
        
    def _on_segment(self, text: str) -> None:
        """
        内部回调处理
        
        Args:
            text: 识别到的文本
        """
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
        
        # 设置客户端回调
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
        
    async def start_recognition_async(self) -> bool:
        """
        异步启动语音识别
        
        Returns:
            bool: 是否成功启动
        """
        if not self.is_initialized:
            if not await self.initialize_async():
                return False
                
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.logger.info("语音识别已在运行")
            return True
        
        # 设置客户端回调
        self.client.add_segment_callback(self._on_segment)
        
        # 在新线程中启动语音识别
        def run_recognition():
            asyncio.run(self.client.start())
            
        self.recognition_thread = threading.Thread(
            target=run_recognition,
            daemon=True
        )
        self.recognition_thread.start()
        
        # 等待一会，确保线程启动
        await asyncio.sleep(1)
        
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
            
        self.recognition_thread = None
        self.logger.info("语音识别已停止")
        
    async def stop_recognition_async(self) -> None:
        """异步停止语音识别"""
        if not self.client:
            return
            
        self.logger.info("停止语音识别...")
        self.client.stop()
        
        # 等待线程结束
        if self.recognition_thread and self.recognition_thread.is_alive():
            for _ in range(20):  # 最多等待2秒
                if not self.recognition_thread.is_alive():
                    break
                await asyncio.sleep(0.1)
            
        self.recognition_thread = None
        self.logger.info("语音识别已停止")

    def is_recognition_active(self) -> bool:
        """
        检查语音识别是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return (self.recognition_thread is not None and 
                self.recognition_thread.is_alive())
                
    def get_last_text(self) -> str:
        """
        获取最后识别的文本
        
        Returns:
            str: 最后识别的文本
        """
        return self.last_text
        
    def update_server_config(self, host: str = None, port: int = None, 
                             use_local_server: bool = None, auto_start_server: bool = None,
                             server_config: Dict[str, Any] = None) -> bool:
        """
        更新服务器配置
        
        Args:
            host: 服务器地址
            port: 服务器端口
            use_local_server: 是否使用本地服务器
            auto_start_server: 是否自动启动本地服务器
            server_config: 服务器详细配置
            
        Returns:
            bool: 是否需要重启服务才能生效
        """
        need_restart = False
        
        # 更新配置
        if host is not None and host != self.settings.get_setting("host"):
            self.settings.update_setting("host", host)
            need_restart = True
            
        if port is not None and port != self.settings.get_setting("port"):
            self.settings.update_setting("port", port)
            need_restart = True
            
        if use_local_server is not None and use_local_server != self.settings.get_setting("use_local_server"):
            self.settings.update_setting("use_local_server", use_local_server)
            need_restart = True
            
        if auto_start_server is not None:
            self.settings.update_setting("auto_start_server", auto_start_server)
            
        if server_config is not None:
            current_config = self.settings.get_setting("server_config")
            updated_config = {**current_config, **server_config}
            self.settings.update_setting("server_config", updated_config)
            if self.is_initialized and self.server_manager:
                need_restart = True
                
        # 保存配置
        self.save_config()
        
        return need_restart
        
    def restart_service(self) -> bool:
        """
        重启STT服务
        
        Returns:
            bool: 是否成功重启
        """
        was_active = self.is_recognition_active()
        
        # 关闭服务
        self.shutdown()
        
        # 重新初始化
        if not self.initialize():
            return False
            
        # 如果之前在运行，则重新启动
        if was_active:
            return self.start_recognition()
            
        return True