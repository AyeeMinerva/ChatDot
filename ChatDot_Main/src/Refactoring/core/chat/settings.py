from core.global_managers.settings_manager import SettingsManager

DEFAULT_CHAT_SETTINGS = {
    "current_handler": "defaultPrompt",  # 默认的上下文处理器
}

class ChatSettings:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("chat", DEFAULT_CHAT_SETTINGS)

    def get_setting(self, key):
        """获取设置值"""
        return self.settings_manager.get_setting("chat", key)

    def update_setting(self, key, value):
        """更新设置值"""
        self.settings_manager.update_setting("chat", key, value)