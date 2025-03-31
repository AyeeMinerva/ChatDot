from global_managers.persistence_manager import PersistenceManager

class TTSPersistence:
    def __init__(self):
        self.persistence_manager = PersistenceManager()

    def save_config(self, config):
        """
        保存 TTS 配置到持久化存储
        """
        self.persistence_manager.save("tts", config)

    def load_config(self):
        """
        从持久化存储加载 TTS 配置
        """
        return self.persistence_manager.load("tts")