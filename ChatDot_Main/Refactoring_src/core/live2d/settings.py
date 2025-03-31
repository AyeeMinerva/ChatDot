from global_managers.settings_manager import SettingsManager

DEFAULT_LIVE2D_SETTINGS = {
    "url": None,  # Live2D 后端的 URL，默认为 None
    "initialize": True  # 是否初始化 Live2D，默认为 True
}

class Live2DSettings:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("live2d", DEFAULT_LIVE2D_SETTINGS)

    def get_setting(self, key):
        """
        获取 Live2D 的某个设置
        """
        return self.settings_manager.get_setting("live2d", key)

    def update_setting(self, key, value):
        """
        更新 Live2D 的某个设置
        """
        self.settings_manager.update_setting("live2d", key, value)