from global_managers.persistence_manager import PersistenceManager

class ContextHandlePersistence:
    def __init__(self):
        self.persistence_manager = PersistenceManager()

    def save_current_handler(self, handler_name: str) -> None:
        """保存当前使用的处理器名称"""
        self.persistence_manager.save("context_handle", {"current_handler": handler_name})

    def load_current_handler(self) -> str:
        """加载上次使用的处理器名称"""
        data = self.persistence_manager.load("context_handle")
        return data.get("current_handler", "defaultPrompt")