from typing import List, Dict
from global_managers.persistence_manager import PersistenceManager
import os
import json
from datetime import datetime

class ChatPersistence:
    # 全局常量定义
    BASE_DIR = "SECRETS"
    HISTORY_DIR = os.path.join(BASE_DIR, "chat_history")
    CURRENT_HISTORY_FILE = "current_history.json"
    EXPORTS_DIR = os.path.join(BASE_DIR, "chat_exports")

    def __init__(self):
        self.persistence_manager = PersistenceManager()

    def save_history(self, messages: List[Dict]):
        """保存当前聊天历史记录"""
        self.persistence_manager.save("chat", messages, self.CURRENT_HISTORY_FILE)

    def load_history(self) -> List[Dict]:
        """加载当前聊天历史记录"""
        return self.persistence_manager.load("chat", self.CURRENT_HISTORY_FILE) or []

    def export_history(self, filepath: str = None, messages: List[Dict] = None):
        """
        导出历史记录到文件
        
        Args:
            filepath: 可选，指定导出文件路径。如果未指定，将使用当前日期时间创建文件名
            messages: 要导出的消息列表
        """
        if filepath is None:
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(self.EXPORTS_DIR, f"chat_history_{current_time}.json")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        return filepath

    def import_history(self, filepath: str) -> List[Dict]:
        """从文件导入历史记录"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"导入历史记录失败: {str(e)}")

    def get_history_list(self) -> List[Dict]:
        """获取历史记录文件列表"""
        history_files = []
        
        exports_dir = self.EXPORTS_DIR
        if os.path.exists(exports_dir):
            for file in os.listdir(exports_dir):
                if file.endswith('.json'):
                    filepath = os.path.join(exports_dir, file)
                    history_files.append({
                        'filename': file,
                        'filepath': filepath,
                        'modified_time': datetime.fromtimestamp(
                            os.path.getmtime(filepath)
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
        return sorted(history_files, 
                     key=lambda x: x['modified_time'], 
                     reverse=True)