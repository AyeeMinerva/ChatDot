from .embedding_service import get_embedding_service
from .vector_store import VectorStore
from .config import get_vector_store_settings, update_settings
from global_managers.logger_manager import LoggerManager
from global_managers.service_manager import ServiceManager
from global_managers.settings_manager import SettingsManager
from global_managers.persistence_manager import PersistenceManager
import os

class RAGService:
    """检索增强生成服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        """初始化RAG服务"""
        if getattr(self, '_initialized', False):
            return
            
        self.logger = LoggerManager().get_logger()
        self.settings_manager = SettingsManager()
        self.persistence_manager = PersistenceManager()
        
        # 加载配置
        self._load_settings()
        
        # 延迟初始化
        self.vector_store = None
        self.embedding_service = None
        self.collection_name = None
        
        self._initialized = False
        
    def _load_settings(self):
        """加载设置"""
        try:
            settings = self.persistence_manager.load("rag", "settings.json") or {}
            self._enabled = settings.get("enabled", True)  # 默认启用
        except Exception as e:
            self.logger.warning(f"加载RAG设置失败，使用默认值: {e}")
            self._enabled = True
    
    def save_config(self):
        """保存当前配置"""
        try:
            settings = self.persistence_manager.load("rag", "settings.json") or {}
            settings["enabled"] = self._enabled
            self.persistence_manager.save("rag", settings, "settings.json")
            self.logger.debug("RAG服务配置已保存")
        except Exception as e:
            self.logger.error(f"保存RAG配置失败: {e}")
        
    def initialize(self):
        """初始化服务，由ServiceManager调用"""
        if self._initialized:
            self.logger.debug("RAG服务已初始化，跳过")
            return
            
        # 如果服务被禁用，跳过初始化
        if not self._enabled:
            self.logger.info("RAG服务已禁用，跳过初始化")
            return
            
        try:
            # 获取配置
            vector_settings = get_vector_store_settings()
            self.collection_name = vector_settings["default_collection"]
            
            # 初始化嵌入服务
            self.embedding_service = get_embedding_service()
            
            # 初始化向量存储
            self.vector_store = VectorStore(collection_name=self.collection_name)
            
            self._initialized = True
            self.logger.info(f"RAG服务初始化成功，使用集合: '{self.collection_name}'")
        except Exception as e:
            self.logger.error(f"RAG服务初始化失败: {e}", exc_info=True)
            raise RuntimeError(f"无法初始化RAG服务: {e}")
    
    def shutdown(self):
        """关闭服务，由ServiceManager调用"""
        if not self._initialized:
            return
            
        self.logger.info("RAG服务关闭中...")
        self._initialized = False
        # 资源清理
        self.vector_store = None
        self.embedding_service = None
    
    def is_enabled(self):
        """检查服务是否启用"""
        return self._enabled
        
    def update_setting(self, key, value):
        """
        更新设置并保存
        
        Args:
            key: 设置键名
            value: 设置值
        """
        try:
            if key == "enabled":
                old_value = self._enabled
                self._enabled = value
                
                # 如果状态发生变化
                if old_value != value:
                    self.save_config()
                    
                    if value:
                        # 启用服务，需要初始化
                        if not self._initialized:
                            try:
                                self.initialize()
                                self.logger.info("RAG服务已启用并初始化")
                            except Exception as e:
                                self.logger.error(f"启用RAG服务失败: {e}")
                    else:
                        # 禁用服务，需要关闭
                        if self._initialized:
                            self.shutdown()
                            self.logger.info("RAG服务已禁用")
                
            elif key == "collection":
                # 切换集合
                if self.switch_collection(value):
                    self.logger.info(f"已切换到集合: {value}")
                else:
                    self.logger.warning(f"切换到集合 {value} 失败")
                    
            elif key == "embedding_model":
                # 更新嵌入模型
                try:
                    update_settings("embedding", "local_model", {"model_name": value})
                    self.logger.info(f"已更新嵌入模型: {value}")
                    
                    # 重新初始化服务以应用新设置
                    if self._initialized:
                        self.shutdown()
                        self.initialize()
                except Exception as e:
                    self.logger.error(f"更新嵌入模型失败: {e}")
                    
            elif key == "search_results":
                # 更新搜索结果数量
                try:
                    update_settings("vector_store", "search_results", value)
                    self.logger.info(f"已更新搜索结果数量: {value}")
                except Exception as e:
                    self.logger.error(f"更新搜索结果数量失败: {e}")
                    
            else:
                self.logger.warning(f"未知的设置项: {key}")
                return
                
            # 保存配置
            self.save_config()
            
        except Exception as e:
            self.logger.error(f"更新设置 {key} 失败: {e}", exc_info=True)
    
    def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._enabled:
            return False
            
        if not self._initialized:
            self.initialize()
            
        return self._initialized
            
    def switch_collection(self, collection_name):
        """切换到不同的集合/数据库"""
        if not self._ensure_initialized():
            return False
        
        if not collection_name:
            self.logger.error("集合名称不能为空")
            return False
            
        try:
            # 获取新集合的向量存储实例
            self.vector_store = VectorStore(collection_name=collection_name)
            self.collection_name = collection_name
            self.logger.info(f"已切换到集合: '{collection_name}'")
            
            # 更新默认集合设置
            update_settings("vector_store", "default_collection", collection_name)
            
            return True
        except Exception as e:
            self.logger.error(f"切换集合失败: {e}", exc_info=True)
            return False

    def store(self, text: str) -> str:
        """
        存储文本到记忆
        
        Args:
            text: 要存储的文本
        
        Returns:
            str: 存储的记录ID，失败返回None
        """
        if not self._ensure_initialized():
            return None
        
        if not text:
            self.logger.warning("尝试添加空文本，已跳过")
            return None
            
        # 生成嵌入
        embedding = self.embedding_service.embed_text(text)
        if not embedding:
            self.logger.error("生成嵌入向量失败")
            return None
            
        # 存储到向量数据库
        try:
            doc_id = self.vector_store.add_document(
                text=text,
                embedding=embedding,
                metadata={"text": text}
            )
            if doc_id:
                self.logger.info(f"文本已存储到集合 '{self.collection_name}'，ID: {doc_id}")
                return doc_id
            else:
                self.logger.error("存储文本失败")
        except Exception as e:
            self.logger.error(f"存储文本时出错: {e}", exc_info=True)
            
        return None
    
    def delete_by_content(self, content: str, threshold: float = 0.95) -> int:
        """
        根据内容删除记忆
        
        Args:
            content: 要匹配的文本内容
            threshold: 匹配阈值
            
        Returns:
            int: 删除的记录数量
        """
        if not self._ensure_initialized():
            return 0
        
        # 生成嵌入向量
        embedding = self.embedding_service.embed_text(content)
        if not embedding:
            self.logger.error("生成匹配文本的嵌入向量失败")
            return 0
        
        # 查找相似的记录
        similar_items = self.vector_store.search_similar(embedding, n_results=10)
        if not similar_items:
            return 0
        
        # 删除匹配的记录
        count = 0
        for item in similar_items:
            stored_text = item['metadata'].get('text', '')
            similarity = 1.0 - item['distance']
            
            # 检查是否满足删除条件
            if similarity >= threshold and content in stored_text:
                if self.vector_store.delete_document(item['id']):
                    count += 1
        
        if count > 0:
            self.logger.info(f"已删除 {count} 条匹配的记忆")
        
        return count

    def retrieve(self, query: str, n_results: int = None) -> str:
        """
        根据查询检索相关记忆
        
        Args:
            query: 查询文本
            n_results: 希望检索的结果数量
            
        Returns:
            str: 格式化后的上下文文本
        """
        if not self._ensure_initialized():
            return ""
        
        if not query:
            return ""

        # 使用配置的检索结果数量
        if n_results is None:
            n_results = get_vector_store_settings()["search_results"]

        # 生成查询嵌入
        query_embedding = self.embedding_service.embed_text(query)
        if not query_embedding:
            self.logger.error("生成查询嵌入失败")
            return ""

        # 搜索相似项
        similar_items = self.vector_store.search_similar(query_embedding, n_results=n_results)

        if not similar_items:
            self.logger.info(f"在集合 '{self.collection_name}' 中未找到相关记忆")
            return ""

        # 简单拼接找到的文本
        memory_texts = []
        self.logger.info(f"检索到 {len(similar_items)} 条相关记忆")
        for item in similar_items:
            text = item['metadata'].get('text', '')
            memory_texts.append(text)

        # 组合上下文
        formatted_context = "\n\n---\n\n".join(memory_texts)
        final_context = f"以下是从记忆中检索到的相关内容:\n\n{formatted_context}\n\n---"
        
        return final_context
    
    def clear_memory(self):
        """清空当前集合中的所有记忆"""
        if not self._ensure_initialized():
            return False
        return self.vector_store.clear_collection()
        
    def get_memory_count(self):
        """获取当前集合中的记忆数量"""
        if not self._ensure_initialized():
            return 0
        return self.vector_store.get_document_count()
        
    def list_collections(self):
        """列出所有可用的集合"""
        return VectorStore.list_collections()

# 向 ServiceManager 注册 RAG 服务
def register_rag_service():
    """向 ServiceManager 注册 RAG 服务"""
    logger = LoggerManager().get_logger()
    service_manager = ServiceManager()
    
    if not service_manager.is_service_registered("rag_service"):
        try:
            # 直接注册 RAGService 类，而不是实例
            service_manager.register_service("rag_service", RAGService)
            logger.info("RAG 服务已注册到 ServiceManager")
        except Exception as e:
            logger.error(f"注册 RAG 服务到 ServiceManager 失败: {e}", exc_info=True)
    else:
        logger.debug("RAG 服务已经注册到 ServiceManager")

# 获取服务实例的函数
def get_rag_service():
    """获取 RAG 服务实例"""
    try:
        # 通过 ServiceManager 获取服务实例
        service_manager = ServiceManager()
        if service_manager.is_service_registered("rag_service"):
            return service_manager.get_service("rag_service")
        else:
            # 如果服务未注册，返回 None
            LoggerManager().get_logger().warning("RAG 服务未注册到 ServiceManager")
            return None
    except Exception as e:
        LoggerManager().get_logger().error(f"获取 RAG 服务失败: {e}", exc_info=True)
        return None