import json
import os
from datetime import datetime

class ChatHistory:
    def __init__(self, directory="ChatDot_Main\history"):
        self.filepath = directory
        # 获取当前时间并格式化日期和时间
        current_date = datetime.now().strftime("%Y%m%d")
        current_time = datetime.now().strftime("%H%M%S")
        counter = 1
        
        # 使用日期和时间作为文件名的一部分
        self.filepath = os.path.join(directory, f"history_{current_date}_{current_time}_{counter}.json")
        
        # 以防万一同一秒内创建多个文件
        while os.path.exists(self.filepath):
            counter += 1
            new_name = f"history_{current_date}_{current_time}_{counter}.json"
            self.filepath = os.path.join(directory, new_name)


    def save_history(self, history):
        try:
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
                    
            self.filepath = file_to_load
            
            return history
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return None
