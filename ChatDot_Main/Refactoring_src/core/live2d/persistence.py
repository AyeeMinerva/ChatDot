from global_managers.persistence_manager import PersistenceManager

class Live2DPersistence:
    def __init__(self):
        self.persistence_manager = PersistenceManager()

    def save_config(self, config):
        """
        保存 Live2D 配置到持久化存储
        """
        self.persistence_manager.save("live2d", config)

    def load_config(self):
        """
        从持久化存储加载 Live2D 配置
        """
        return self.persistence_manager.load("live2d")