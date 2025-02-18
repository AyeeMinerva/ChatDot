import json
import os
import sys

# 将项目根目录添加到模块搜索路径中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.path_utils import get_project_root

SETTINGS_FILE = "SECRETS/user_settings.json"

def load_settings():
    settings_path = os.path.join(get_project_root(), SETTINGS_FILE)
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
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
    settings_path = os.path.join(get_project_root(), SETTINGS_FILE)
    # 确保目录存在
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存用户设置失败: {e}")

if __name__ == "__main__":
    # 示例设置
    example_settings = {
        'api_key': 'YOUR_API_KEY',
        'api_base': 'https://api.example.com',
        'model_name': 'gpt-3.5-turbo',
        'model_params': {'temperature': 0.7, 'max_tokens': 200},
        'model_list': ['gpt-3.5-turbo', 'gpt-4']
    }

    # 保存设置
    save_settings(example_settings)
    print("设置已保存")

    # 加载设置
    loaded_settings = load_settings()
    print("加载的设置:", loaded_settings)

    # 检查设置是否正确加载
    if loaded_settings == example_settings:
        print("设置已正确保存和加载")
    else:
        print("设置保存或加载失败")