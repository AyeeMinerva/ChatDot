import json
import os

class PersistenceManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PersistenceManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.data = {}
        return cls._instance

    def save(self, module_name, data, filename="data.json"):
        """保存模块的数据到文件"""
        directory = os.path.join("persistence", module_name)
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load(self, module_name, filename="data.json"):
        """从文件加载模块的数据"""
        filepath = os.path.join("persistence", module_name, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}