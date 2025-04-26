from global_managers.persistence_manager import PersistenceManager

class TTSHandlePersistence:
    """TTS处理器持久化类"""
    
    def __init__(self):
        self.persistence_manager = PersistenceManager()
        
    def save_current_handler(self, handler_name: str) -> None:
        """保存当前使用的处理器名称"""
        self.persistence_manager.save("tts_handle_current", handler_name)
        
    def load_current_handler(self) -> str:
        """加载当前使用的处理器名称"""
        return self.persistence_manager.load("tts_handle_current") or "sentence"