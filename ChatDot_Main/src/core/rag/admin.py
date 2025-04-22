from .config import get_rag_settings, set_api_key, get_api_key
from .vector_store import VectorStore
from global_managers.logger_manager import LoggerManager
from global_managers.settings_manager import SettingsManager
import os

class RAGAdmin:
    """RAG 系统管理工具，提供配置和数据库管理功能"""
    
    def __init__(self):
        self.logger = LoggerManager().get_logger()
        self.settings_manager = SettingsManager()
    
    def get_rag_settings(self):
        """获取 RAG 模块的当前设置"""
        return get_rag_settings()
    
    def set_embedding_mode(self, mode: str) -> bool:
        """设置嵌入模式（'local' 或 'api'）"""
        if mode not in ["local", "api"]:
            self.logger.error(f"不支持的嵌入模式: {mode}，必须是 'local' 或 'api'")
            return False
            
        try:
            settings = get_rag_settings()
            settings["embedding"]["mode"] = mode
            self.settings_manager.update_setting("rag", "embedding", settings["embedding"])
            self.logger.info(f"嵌入模式已设置为: {mode}")
            return True
        except Exception as e:
            self.logger.error(f"设置嵌入模式失败: {e}", exc_info=True)
            return False
    
    def set_local_model(self, model_name: str) -> bool:
        """设置本地嵌入模型"""
        try:
            settings = get_rag_settings()
            settings["embedding"]["local_model"]["model_name"] = model_name
            self.settings_manager.update_setting("rag", "embedding", settings["embedding"])
            self.logger.info(f"本地嵌入模型已设置为: {model_name}")
            return True
        except Exception as e:
            self.logger.error(f"设置本地嵌入模型失败: {e}", exc_info=True)
            return False
    
    def set_api_model(self, provider: str, model: str, api_base: str = "") -> bool:
        """设置 API 嵌入模型"""
        if provider not in ["openai", "gemini", "custom"]:
            self.logger.warning(f"未知的 API 提供商: {provider}")
        
        try:
            settings = get_rag_settings()
            settings["embedding"]["api"]["provider"] = provider
            settings["embedding"]["api"]["model"] = model
            if api_base:
                settings["embedding"]["api"]["api_base"] = api_base
            self.settings_manager.update_setting("rag", "embedding", settings["embedding"])
            self.logger.info(f"API 嵌入模型已设置为 {provider}:{model}")
            return True
        except Exception as e:
            self.logger.error(f"设置 API 嵌入模型失败: {e}", exc_info=True)
            return False
    
    def manage_api_key(self, provider: str, key: str = None) -> bool | str:
        """
        管理 API 密钥。
        如果提供了 key，则设置密钥。否则，返回当前密钥。
        """
        if key is not None:
            # 设置密钥
            return set_api_key(provider, key)
        else:
            # 获取密钥
            api_key = get_api_key(provider)
            if api_key:
                # 返回掩码密钥
                masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                return masked_key
            else:
                return ""
    
    def set_default_collection(self, name: str) -> bool:
        """设置默认集合名称"""
        try:
            settings = get_rag_settings()
            settings["vector_store"]["default_collection"] = name
            self.settings_manager.update_setting("rag", "vector_store", settings["vector_store"])
            self.logger.info(f"默认集合已设置为: {name}")
            return True
        except Exception as e:
            self.logger.error(f"设置默认集合失败: {e}", exc_info=True)
            return False
    
    def list_collections(self) -> list[str]:
        """列出所有可用的集合"""
        return VectorStore.list_collections()
    
    def create_collection(self, name: str) -> bool:
        """创建新集合"""
        try:
            # 通过初始化一个集合实例来创建它
            VectorStore(collection_name=name)
            self.logger.info(f"已创建集合: {name}")
            return True
        except Exception as e:
            self.logger.error(f"创建集合失败: {e}", exc_info=True)
            return False
    
    def delete_collection(self, name: str) -> bool:
        """删除集合"""
        try:
            vector_store = VectorStore(collection_name=name)
            result = vector_store.delete_collection()
            if result:
                self.logger.info(f"已删除集合: {name}")
            return result
        except Exception as e:
            self.logger.error(f"删除集合失败: {e}", exc_info=True)
            return False
    
    def get_collection_stats(self, name: str = None) -> dict:
        """获取集合统计信息"""
        try:
            if name is None:
                # 获取所有集合的统计信息
                collections = self.list_collections()
                stats = {}
                for collection_name in collections:
                    vector_store = VectorStore(collection_name=collection_name)
                    stats[collection_name] = {
                        "document_count": vector_store.get_document_count()
                    }
                return stats
            else:
                # 获取指定集合的统计信息
                vector_store = VectorStore(collection_name=name)
                return {
                    "document_count": vector_store.get_document_count()
                }
        except Exception as e:
            self.logger.error(f"获取集合统计信息失败: {e}", exc_info=True)
            return {}