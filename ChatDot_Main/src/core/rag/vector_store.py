import chromadb
from chromadb.config import Settings
import chromadb.proto
from global_managers.logger_manager import LoggerManager
from .config import get_vector_store_settings
import os
import uuid
from datetime import datetime

class VectorStore:
    _instances = {}  # 用于存储不同集合名的实例

    def __new__(cls, collection_name=None, persist_directory=None):
        # 从配置获取默认值
        settings = get_vector_store_settings()
        collection_name = collection_name or settings["default_collection"]
        
        # 使用集合名称作为实例缓存的键
        key = f"{collection_name}:{persist_directory or settings['persist_directory']}"
        
        if key not in cls._instances:
            instance = super(VectorStore, cls).__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, collection_name=None, persist_directory=None):
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return
            
        self.logger = LoggerManager().get_logger()
        
        # 从配置获取设置
        settings = get_vector_store_settings()
        self.persist_directory = persist_directory or settings["persist_directory"]
        self.collection_name = collection_name or settings["default_collection"]
        
        # 确保存储目录存在
        os.makedirs(self.persist_directory, exist_ok=True)

        try:
            self.adapter = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)  # 禁用匿名遥测
            )
            # 获取或创建集合
            self.collection = self.adapter.get_or_create_collection(name=self.collection_name)
            self.logger.info(f"ChromaDB 客户端已连接，使用集合 '{self.collection_name}'，存储于 '{self.persist_directory}'")
            self._initialized = True
        except Exception as e:
            self.logger.error(f"初始化 ChromaDB 失败: {e}", exc_info=True)
            self.adapter = None
            self.collection = None
            raise ConnectionError(f"无法连接到 ChromaDB: {e}")

    def add_qa_pair(self, question: str, answer: str, embedding: list[float], qa_id: str = None) -> str | None:
        """
        添加一个问答对及其嵌入向量到数据库。
        Args:
            question: 问题文本。
            answer: 答案文本。
            embedding: 问答对组合文本的嵌入向量。
            qa_id: 可选，指定唯一ID，否则自动生成。
        Returns:
            存储的文档 ID，如果失败则返回 None。
        """
        if not self.collection or embedding is None:
            self.logger.error("无法添加 Q&A 对：数据库未初始化或 embedding 为空。")
            return None

        if qa_id is None:
            qa_id = str(uuid.uuid4())  # 生成唯一 ID

        # 将 Q&A 存储在元数据中
        metadata = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "collection": self.collection_name
        }
        # 组合文本作为 document
        document_text = f"Q: {question}\nA: {answer}"

        try:
            self.collection.add(
                embeddings=[embedding],
                documents=[document_text],
                metadatas=[metadata],
                ids=[qa_id]
            )
            self.logger.debug(f"成功添加 Q&A 对到 ChromaDB 集合 '{self.collection_name}', ID: {qa_id}")
            return qa_id
        except Exception as e:
            self.logger.error(f"添加 Q&A 对到 ChromaDB 失败 (ID: {qa_id}): {e}", exc_info=True)
            return None

    def search_similar(self, query_embedding: list[float], n_results: int = None) -> list[dict]:
        """
        根据查询向量搜索相似的问答对。
        Args:
            query_embedding: 查询文本的嵌入向量。
            n_results: 返回结果的数量，默认使用配置值。
        Returns:
            相似文档的列表，每个文档包含 'id', 'metadata', 'distance', 'document'。
            如果失败或无结果，返回空列表。
        """
        if not self.collection or query_embedding is None:
            self.logger.error("无法搜索：数据库未初始化或查询 embedding 为空。")
            return []
        
        if self.collection.count() == 0:
            self.logger.debug(f"集合 '{self.collection_name}' 为空，无法执行搜索。")
            return []

        # 如果未提供 n_results，使用配置值
        if n_results is None:
            n_results = get_vector_store_settings()["search_results"]

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self.collection.count()),
                include=['metadatas', 'documents', 'distances']
            )
            self.logger.debug(f"ChromaDB 查询完成，在集合 '{self.collection_name}' 中找到 {len(results.get('ids', [[]])[0])} 个结果。")

            # 解析结果并返回更友好的格式
            formatted_results = []
            ids = results.get('ids', [[]])[0]
            distances = results.get('distances', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            documents = results.get('documents', [[]])[0]

            for i, doc_id in enumerate(ids):
                formatted_results.append({
                    "id": doc_id,
                    "distance": distances[i],
                    "metadata": metadatas[i],
                    "document": documents[i]
                })
            
            # 按距离排序
            formatted_results.sort(key=lambda x: x['distance'])
            
            return formatted_results

        except Exception as e:
            self.logger.error(f"在 ChromaDB 集合 '{self.collection_name}' 中搜索失败: {e}", exc_info=True)
            return []

    def find_similar_qa_pairs(self, question: str, answer: str = None, threshold: float = 0.9) -> list:
        """
        查找与给定问题和答案相似的问答对
        
        Args:
            question: 要查找的问题
            answer: 要查找的答案，可选
            threshold: 相似度阈值，越高要求越相似
        
        Returns:
            符合条件的问答对列表，每项包含id和元数据
        """
        if not self.collection:
            self.logger.error("数据库未初始化，无法查找问答对")
            return []
            
        try:
            # 构建查询文本
            query_text = question
            if answer:
                query_text = f"Question: {question}\nAnswer: {answer}"
                
            # 通过关键词查询
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(10, self.collection.count()),  # 限制结果数量
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not results["ids"] or not results["ids"][0]:
                return []
                
            # 整理结果
            matches = []
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else 1.0
                
                # 检查相似度是否达到阈值
                similarity = 1.0 - distance  # 距离越小，相似度越高
                if similarity >= threshold:
                    matches.append({
                        "id": doc_id,
                        "metadata": metadata,
                        "similarity": similarity
                    })
                    
            return matches
        except Exception as e:
            self.logger.error(f"查找问答对时出错: {e}", exc_info=True)
            return []
    
    def delete_qa_by_content(self, question: str, answer: str = None, threshold: float = 0.9) -> int:
        """
        根据问题和答案内容删除问答对
        
        Args:
            question: 要删除的问题
            answer: 要删除的答案，可选
            threshold: 相似度阈值，越高要求越相似
        
        Returns:
            删除的记录数量
        """
        if not self.collection:
            self.logger.error("数据库未初始化，无法删除问答对")
            return 0
            
        try:
            # 查找匹配的问答对
            matches = self.find_similar_qa_pairs(question, answer, threshold)
            
            if not matches:
                self.logger.info("未找到匹配的问答对")
                return 0
                
            # 提取ID列表
            ids_to_delete = [match["id"] for match in matches]
            
            # 执行删除
            self.collection.delete(ids=ids_to_delete)
            
            self.logger.info(f"已删除 {len(ids_to_delete)} 条匹配的问答对")
            return len(ids_to_delete)
        except Exception as e:
            self.logger.error(f"删除问答对时出错: {e}", exc_info=True)
            return 0

    def get_document_count(self) -> int:
        """返回数据库中的文档数量"""
        if not self.collection:
            return 0
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"获取 ChromaDB 集合 '{self.collection_name}' 文档计数失败: {e}", exc_info=True)
            return 0
            
    def clear_collection(self) -> bool:
        """清空当前集合中的所有数据"""
        if not self.collection:
            self.logger.error("数据库未初始化，无法清空集合。")
            return False
            
        try:
            # 获取所有 ID
            count = self.collection.count()
            if count == 0:
                self.logger.info(f"集合 '{self.collection_name}' 已经为空。")
                return True
                
            # 删除集合并重新创建
            self.adapter.delete_collection(self.collection_name)
            self.collection = self.adapter.create_collection(name=self.collection_name)
            
            self.logger.info(f"已清空集合 '{self.collection_name}'，删除了 {count} 条记录。")
            return True
        except Exception as e:
            self.logger.error(f"清空集合 '{self.collection_name}' 失败: {e}", exc_info=True)
            return False
            
    def delete_collection(self) -> bool:
        """删除整个集合"""
        if not self.adapter:
            self.logger.error("ChromaDB 客户端未初始化，无法删除集合。")
            return False
            
        try:
            self.adapter.delete_collection(self.collection_name)
            self.logger.info(f"已删除集合 '{self.collection_name}'。")
            # 从类实例缓存中移除
            key = f"{self.collection_name}:{self.persist_directory}"
            if key in self.__class__._instances:
                del self.__class__._instances[key]
            return True
        except Exception as e:
            self.logger.error(f"删除集合 '{self.collection_name}' 失败: {e}", exc_info=True)
            return False
            
    @classmethod
    def list_collections(cls, persist_directory=None) -> list[str]:
        """列出所有可用的集合"""
        logger = LoggerManager().get_logger()
        
        if not persist_directory:
            persist_directory = get_vector_store_settings()["persist_directory"]
            
        try:
            # 确保目录存在
            if not os.path.exists(persist_directory):
                logger.info(f"向量存储目录 '{persist_directory}' 不存在，返回空列表。")
                return []
                
            adapter = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            collections = adapter.list_collections()
            collection_names = [col.name for col in collections]
            logger.info(f"获取到 {len(collection_names)} 个集合: {', '.join(collection_names)}")
            return collection_names
        except Exception as e:
            logger.error(f"列出集合失败: {e}", exc_info=True)
            return []