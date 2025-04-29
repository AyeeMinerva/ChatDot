from global_managers.persistence_manager import PersistenceManager
from global_managers.logger_manager import LoggerManager

class LLMPersistence:
    def __init__(self):
        self.persistence_manager = PersistenceManager()

    def save_config(self, config):
        """保存 LLM 配置到持久化存储"""
        self.persistence_manager.save("llm", config)

    def load_config(self):
        """从持久化存储加载 LLM 配置"""
        return self.persistence_manager.load("llm")