"""
STT模块的设置管理
"""
from global_managers.settings_manager import SettingsManager
from global_managers.persistence_manager import PersistenceManager

class STTSettings:
    """STT模块的设置类"""
    
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.persistence_manager = PersistenceManager()
        
        # 注册默认设置
        self._register_default_settings()
        
        # 加载持久化设置
        self._load_persisted_settings()
    
    def _register_default_settings(self):
        """注册默认设置"""
        default_settings = {
            "enabled": True,         # 是否启用STT服务
            "host": "localhost",     # 服务器地址
            "port": 10095,           # 服务器端口
            "use_ssl": False         # 是否使用SSL
        }
        self.settings_manager.register_module("stt", default_settings)
    
    def _load_persisted_settings(self):
        """从持久化存储加载设置"""
        persisted_settings = self.persistence_manager.load("stt")
        for key, value in persisted_settings.items():
            self.update_setting(key, value)
    
    def get_setting(self, key):
        """获取设置值"""
        return self.settings_manager.get_setting("stt", key)
    
    def update_setting(self, key, value):
        """更新设置值"""
        self.settings_manager.update_setting("stt", key, value)
        
        # 保存到持久化存储
        settings = {}
        settings[key] = value
        self.persistence_manager.save("stt", settings)