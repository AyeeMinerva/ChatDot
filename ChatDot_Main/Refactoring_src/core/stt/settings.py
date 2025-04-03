"""
STT模块的设置管理
"""
from global_managers.settings_manager import SettingsManager
from global_managers.logger_manager import LoggerManager

DEFAULT_SETTINGS = {
    # 基本设置
    "enabled": True,                # 是否启用STT服务
    "host": "localhost",            # 服务器地址
    "port": 10095,                  # 服务器端口
    "use_ssl": False,               # 是否使用SSL
    
    # 音频收集设置
    "volume_threshold": 300,       # 音量阈值，0-32767之间的值，越小越灵敏
    "silence_timeout": 1.5,        # 沉默超时时间(秒)，多久没有声音就中断当前语音片段
    
    # 服务器设置
    "use_local_server": True,       # 是否使用本地服务器
    "auto_start_server": True,      # 是否自动启动本地服务器
    
    # 服务器配置
    "server_config": {
        "device": "cuda",           # 设备：cuda或cpu
        "ngpu": 1,                  # GPU数量
        "ncpu": 4,                  # CPU核心数
        
        # 模型配置
        "models": {
            "asr_model": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            "asr_model_revision": "v2.0.4",
            "asr_model_online": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
            "asr_model_online_revision": "v2.0.4",
            "vad_model": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
            "vad_model_revision": "v2.0.4",
            "punc_model": "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727",
            "punc_model_revision": "v2.0.4"
        }
    }
}

class STTSettings:
    """STT模块的设置类"""
    
    def __init__(self):
        """初始化STT设置"""
        self.settings_manager = SettingsManager()
        self.logger = LoggerManager().get_logger()
        
        # 注册默认设置
        self._register_default_settings()
        
        # 输出当前配置信息
        self.logger.debug(f"当前STT服务配置: host={self.get_setting('host')}, "
                         f"port={self.get_setting('port')}, "
                         f"use_local_server={self.get_setting('use_local_server')}")
    
    def _register_default_settings(self):
        """注册默认设置"""
        self.settings_manager.register_module("stt", DEFAULT_SETTINGS)
    
    def get_setting(self, key):
        """
        获取设置值
        
        Args:
            key: 设置键名
            
        Returns:
            设置值
        """
        return self.settings_manager.get_setting("stt", key)
    
    def update_setting(self, key, value):
        """
        更新设置值
        
        Args:
            key: 设置键名
            value: 设置值
        """
        self.settings_manager.update_setting("stt", key, value)
        
        # 记录配置更改
        if key in ["host", "port", "use_ssl", "use_local_server", "auto_start_server"]:
            self.logger.debug(f"更新STT设置: {key}={value}")