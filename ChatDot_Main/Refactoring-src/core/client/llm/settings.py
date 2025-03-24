from global_managers.settings_manager import SettingsManager

DEFAULT_LLM_SETTINGS = {
    "api_keys": [],
    "api_base": "",
    "model_name": "gpt-3.5-turbo",
    "model_params": {
        "temperature": 0.7,
        "max_tokens": 200,
        "stream": True
    }
}

class LLMSettings:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("llm", DEFAULT_LLM_SETTINGS)

    def get_setting(self, key):
        return self.settings_manager.get_setting("llm", key)

    def update_setting(self, key, value):
        self.settings_manager.update_setting("llm", key, value)