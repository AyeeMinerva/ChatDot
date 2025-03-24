from core.client.llm.client import LLMClient
from core.client.llm.settings import LLMSettings
from core.client.llm.persistence import LLMPersistence
from core.client.llm.worker import LLMWorker

class LLMService:
    def __init__(self):
        self.client = LLMClient()
        self.settings = LLMSettings()
        self.persistence = LLMPersistence()

    def initialize(self):
        """初始化服务，加载配置并设置 LLMClient"""
        config = self.persistence.load_config()
        if config:
            for key, value in config.items():
                self.settings.update_setting(key, value)

        api_keys = self.settings.get_setting("api_keys")
        api_base = self.settings.get_setting("api_base")
        self.client.set_api_config(api_keys, api_base, test_connection=False)

        model_name = self.settings.get_setting("model_name")
        model_params = self.settings.get_setting("model_params")
        self.client.set_model_name(model_name)
        self.client.set_model_params(model_params)

    def save_config(self):
        """保存当前配置"""
        config = {
            "api_keys": self.settings.get_setting("api_keys"),
            "api_base": self.settings.get_setting("api_base"),
            "model_name": self.settings.get_setting("model_name"),
            "model_params": self.settings.get_setting("model_params")
        }
        self.persistence.save_config(config)

    def send_message_async(self, messages, model_name=None, model_params_override=None, 
                           on_complete=None, on_error=None, on_stream=None):
        """异步发送消息到 LLM"""
        worker = LLMWorker(
            llm_client=self.client,
            messages=messages,
            model_name=model_name,
            model_params_override=model_params_override,
            on_complete=on_complete,
            on_error=on_error,
            on_stream=on_stream
        )
        worker.start()

    def send_message(self, messages, model_name=None, model_params_override=None):
        """同步发送消息到 LLM"""
        return self.client.communicate(messages, model_name, model_params_override)

    def fetch_models(self):
        """获取可用模型列表"""
        return self.client.fetch_available_models()

    def update_setting(self, key, value):
        """更新设置并保存"""
        self.settings.update_setting(key, value)
        self.save_config()