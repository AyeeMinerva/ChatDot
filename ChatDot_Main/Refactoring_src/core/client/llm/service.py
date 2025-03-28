from typing import Dict, Iterator, List
from global_managers.service_manager import ServiceManager
from client.llm.client import LLMClient
from client.llm.settings import LLMSettings
from client.llm.persistence import LLMPersistence
from client.llm.worker import LLMWorker

class LLMService:
    def __init__(self):
        self.service_manager = ServiceManager()
        self.settings = LLMSettings()
        self.persistence = LLMPersistence()
        self.client = LLMClient()

    def initialize(self):
        """初始化服务"""
        config = self.persistence.load_config()
        if config:
            for key, value in config.items():
                self.settings.update_setting(key, value)

        # 初始化客户端配置
        self._initialize_client_config()
        
    def _initialize_client_config(self):
        """初始化客户端配置"""
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

    def send_message(self, messages: List[Dict], model_name: str = None, 
                    model_params: Dict = None) -> Iterator[str]:
        """
        发送消息到LLM并返回响应迭代器
        
        Args:
            messages: 消息列表
            model_name: 可选的模型名称
            model_params: 可选的模型参数

        Returns:
            Iterator[str]: 响应迭代器
        """
        worker = LLMWorker(
            llm_client=self.client,
            messages=messages,
            model_name=model_name,
            model_params=model_params
        )
        worker.start()
        #worker.join()  # 等待响应完成（此操作会导致阻塞）
        # 返回一个实时的响应迭代器
        return worker.get_response()
    
    def fetch_models(self):
        """获取可用模型列表"""
        return self.client.fetch_available_models()

    def update_setting(self, key, value):
        """更新设置并保存"""
        self.settings.update_setting(key, value)
        #调用client的set_api_config方法
        # 根据不同的设置类型调用对应的配置方法
        if key in ["api_keys", "api_base"]:
            # 更新API配置
            api_keys = self.settings.get_setting("api_keys")
            api_base = self.settings.get_setting("api_base")
            self.client.set_api_config(api_keys, api_base, test_connection=False)
        elif key == "model_name":
            # 更新模型名称
            self.client.set_model_name(value)
        elif key == "model_params":
            # 更新模型参数
            self.client.set_model_params(value)
        self.save_config()