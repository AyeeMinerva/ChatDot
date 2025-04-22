from global_managers.settings_manager import SettingsManager
from global_managers.persistence_manager import PersistenceManager
from global_managers.logger_manager import LoggerManager
from utils.path_utils import get_core_path
import os
import json

# RAG 模块的默认设置
DEFAULT_SETTINGS = {
    "enabled": True,  # 服务启用状态
    "embedding": {
        "mode": "local",  # local 或 api
        "local_model": {
            "model_name": "all-MiniLM-L6-v2",
            "cache_dir": os.path.join(get_core_path(), "rag", "models")
        },
        "api": {
            "provider": "openai",  # openai, gemini 或 custom
            "model": "text-embedding-ada-002",
            "api_base": "",  # 自定义API基础URL
            "timeout": 30
        }
    },
    "vector_store": {
        "persist_directory": os.path.join(get_core_path(), "SECRETS", "persistence", "rag_vector_store"),
        "default_collection": "chat_memory",
        "search_results": 3,  # 默认检索结果数量
        "similarity_threshold": 0.95  # 相似度阈值,用于删除操作
    }
}

# API 密钥的持久化数据结构
DEFAULT_API_KEYS = {
    "openai": "",
    "gemini": "",
    "custom": ""  # 自定义 API 提供商的密钥
}

# 初始化
logger = LoggerManager().get_logger()
settings_manager = SettingsManager()
persistence_manager = PersistenceManager()

# 注册设置
settings_manager.register_module("rag", DEFAULT_SETTINGS)

def get_rag_settings():
    """获取 RAG 模块的所有设置"""
    return settings_manager.settings.get("rag", DEFAULT_SETTINGS)

def get_embedding_settings():
    """获取嵌入相关设置"""
    return get_rag_settings().get("embedding", DEFAULT_SETTINGS["embedding"])

def get_vector_store_settings():
    """获取向量存储相关设置"""
    return get_rag_settings().get("vector_store", DEFAULT_SETTINGS["vector_store"])

def save_api_keys(api_keys):
    """安全保存 API 密钥"""
    try:
        persistence_manager.save("rag", api_keys, "api_keys.json")
        logger.info("API 密钥已安全保存")
        return True
    except Exception as e:
        logger.error(f"保存 API 密钥失败: {e}", exc_info=True)
        return False

def load_api_keys():
    """加载 API 密钥"""
    try:
        api_keys = persistence_manager.load("rag", "api_keys.json")
        if not api_keys:
            # 首次使用，创建默认结构但不保存
            api_keys = DEFAULT_API_KEYS
        return api_keys
    except Exception as e:
        logger.error(f"加载 API 密钥失败: {e}", exc_info=True)
        return DEFAULT_API_KEYS

def get_api_key(provider="openai"):
    """获取特定提供商的 API 密钥"""
    api_keys = load_api_keys()
    return api_keys.get(provider, "")

def set_api_key(provider, key):
    """设置特定提供商的 API 密钥"""
    api_keys = load_api_keys()
    api_keys[provider] = key
    return save_api_keys(api_keys)

def update_settings(module, key, value):
    """更新设置"""
    if module not in get_rag_settings():
        logger.error(f"无效的设置模块: {module}")
        return False
    
    if key not in get_rag_settings()[module]:
        logger.error(f"无效的设置键: {key}")
        return False
    
    try:
        settings_manager.update_setting("rag", module, {**get_rag_settings()[module], key: value})
        logger.info(f"设置已更新: {module}.{key}")
        return True
    except Exception as e:
        logger.error(f"更新设置失败: {e}", exc_info=True)
        return False