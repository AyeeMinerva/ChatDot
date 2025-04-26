from global_managers.settings_manager import SettingsManager

DEFAULT_TTS_HANDLE_SETTINGS = {
    "default_handler": "sentence"
}

class TTSHandleSettings:
    """TTS处理器设置类"""
    
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("tts_handle", DEFAULT_TTS_HANDLE_SETTINGS)
        
    def get_setting(self, key):
        """获取设置值"""
        return self.settings_manager.get_setting("tts_handle", key)
        
    def update_setting(self, key, value):
        """更新设置值"""
        self.settings_manager.update_setting("tts_handle", key, value)