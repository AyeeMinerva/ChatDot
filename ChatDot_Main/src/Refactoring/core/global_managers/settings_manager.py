class SettingsManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SettingsManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.settings = {}
        return cls._instance

    def register_module(self, module_name, default_settings):
        """注册模块的默认设置"""
        if module_name not in self.settings:
            self.settings[module_name] = default_settings

    def get_setting(self, module_name, key):
        """获取模块的某个设置"""
        return self.settings.get(module_name, {}).get(key)

    def update_setting(self, module_name, key, value):
        """更新模块的某个设置"""
        if module_name in self.settings:
            self.settings[module_name][key] = value