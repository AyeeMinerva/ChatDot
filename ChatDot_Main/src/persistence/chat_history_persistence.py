import json
import os

class ChatHistory:
    def __init__(self, directory="ChatDot_Main\history"):
        self.filepath = directory
        counter = 1
        self.filepath = os.path.join(directory, f"history_{counter}.json")
        while os.path.exists(self.filepath):
            counter += 1
            new_name = f"history_{counter}.json"
            self.filepath = os.path.join(directory, new_name)


    def save_history(self, history):
        try:
            # Filter out system messages
            filtered_history = [msg for msg in history if msg["role"] != "system"]
            
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving chat history: {e}")

    def load_history(self, filepath=None):
        try:
            file_to_load = filepath or self.filepath
            with open(file_to_load, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
            # 验证是否为有效的聊天历史记录
            if not isinstance(history, list):
                return None
                
            # 检查是否包含必要的消息格式
            for msg in history:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    return None
                if msg["role"] not in ["system", "user", "assistant"]:
                    return None
                    
            return history
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return None
