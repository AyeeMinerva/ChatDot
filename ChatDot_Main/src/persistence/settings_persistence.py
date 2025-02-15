import json
import os

SETTINGS_FILE = "user_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # 确保返回的设置中包含所有必要的键
                settings.setdefault('api_key', '')
                settings.setdefault('api_base', '')
                settings.setdefault('model_name', '')
                settings.setdefault('model_params', {})
                settings.setdefault('model_list', [])
                return settings
        except Exception as e:
            print(f"加载用户设置失败: {e}")
    return {
        'api_key': '',
        'api_base': '',
        'model_name': '',
        'model_params': {},
        'model_list': []
    }

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存用户设置失败: {e}")
