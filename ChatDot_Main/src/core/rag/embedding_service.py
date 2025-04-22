from sentence_transformers import SentenceTransformer
from global_managers.logger_manager import LoggerManager
from .config import get_embedding_settings, get_api_key
import os
import requests
import json
import time

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.logger = LoggerManager().get_logger()
            cls._instance.settings = get_embedding_settings()
            cls._instance.mode = cls._instance.settings["mode"]
            cls._instance.model = None
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化嵌入服务，根据配置选择本地模型或 API"""
        if self.mode == "local":
            self._initialize_local_model()
        elif self.mode == "api":
            self._initialize_api()
        else:
            self.logger.error(f"不支持的嵌入模式: {self.mode}")
            raise ValueError(f"不支持的嵌入模式: {self.mode}")

    def _initialize_local_model(self):
        """初始化本地嵌入模型"""
        try:
            local_settings = self.settings["local_model"]
            model_name = local_settings["model_name"]
            cache_dir = local_settings["cache_dir"]
            
            # 确保缓存目录存在
            os.makedirs(cache_dir, exist_ok=True)
            
            self.logger.info(f"正在加载本地嵌入模型: {model_name}...")
            self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
            self.logger.info(f"本地嵌入模型 '{model_name}' 加载成功。")
        except Exception as e:
            self.logger.error(f"加载本地嵌入模型失败: {e}", exc_info=True)
            self.model = None
            raise RuntimeError(f"无法加载本地嵌入模型: {e}")

    def _initialize_api(self):
        """初始化 API 设置（仅验证配置，不实际调用 API）"""
        api_settings = self.settings["api"]
        provider = api_settings["provider"]
        model = api_settings["model"]
        
        # 检查 API 密钥
        api_key = get_api_key(provider)
        if not api_key:
            self.logger.warning(f"未设置 {provider} API 密钥，API 嵌入可能无法正常工作")
        
        self.logger.info(f"API 嵌入服务初始化完成，使用提供商: {provider}，模型: {model}")
        # API 模式无需预先加载模型，所以 self.model 保持为 None

    def embed_text(self, text: str) -> list[float] | None:
        """将单个文本字符串嵌入为向量"""
        if not text:
            self.logger.warning("尝试嵌入空文本")
            return None
            
        if self.mode == "local":
            return self._local_embed_text(text)
        elif self.mode == "api":
            return self._api_embed_text(text)
        else:
            self.logger.error(f"不支持的嵌入模式: {self.mode}")
            return None

    def _local_embed_text(self, text: str) -> list[float] | None:
        """使用本地模型嵌入文本"""
        if not self.model:
            self.logger.error("本地嵌入模型未初始化，无法嵌入文本")
            return None
            
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"本地文本嵌入失败: {e}", exc_info=True)
            return None

    def _api_embed_text(self, text: str) -> list[float] | None:
        """使用 API 嵌入文本"""
        api_settings = self.settings["api"]
        provider = api_settings["provider"]
        model = api_settings["model"]
        api_base = api_settings["api_base"]
        timeout = api_settings["timeout"]
        
        # 获取 API 密钥
        api_key = get_api_key(provider)
        if not api_key:
            self.logger.error(f"未设置 {provider} API 密钥，无法进行 API 嵌入")
            return None
            
        # 构建请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 根据提供商确定 API 端点和请求格式
        if provider == "openai" or provider == "custom":
            # 使用 OpenAI 兼容格式
            url = api_base if api_base else "https://api.openai.com/v1/embeddings"
            payload = {
                "model": model,
                "input": text
            }
        elif provider == "gemini":
            # Gemini API 可能有不同的端点和格式
            url = api_base if api_base else "https://generativelanguage.googleapis.com/v1/models"
            url = f"{url}/{model}:embedContent"
            
            # 对于 Gemini，API 密钥通常作为查询参数
            url = f"{url}?key={api_key}"
            
            payload = {
                "content": {"parts": [{"text": text}]}
            }
            
            # 移除授权头
            headers.pop("Authorization", None)
        else:
            self.logger.error(f"不支持的 API 提供商: {provider}")
            return None
            
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                self.logger.error(f"API 嵌入请求失败: 状态码 {response.status_code}, 响应: {response.text}")
                return None
                
            # 解析响应
            data = response.json()
            
            # 根据提供商提取嵌入向量
            if provider == "openai" or provider == "custom":
                embedding = data.get("data", [{}])[0].get("embedding")
            elif provider == "gemini":
                embedding = data.get("embedding", {}).get("values")
            
            if not embedding:
                self.logger.error(f"无法从 API 响应中提取嵌入向量: {data}")
                return None
                
            self.logger.debug(f"API 嵌入成功，耗时: {elapsed:.2f}秒，向量维度: {len(embedding)}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"API 嵌入请求异常: {e}", exc_info=True)
            return None

    def embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        """将文本字符串列表批量嵌入为向量列表"""
        if not texts:
            return []
            
        if self.mode == "local":
            return self._local_embed_texts(texts)
        elif self.mode == "api":
            # API 模式下逐个处理文本，因为不同 API 的批处理逻辑可能不同
            embeddings = []
            for text in texts:
                embedding = self._api_embed_text(text)
                if embedding:
                    embeddings.append(embedding)
                else:
                    # 如果某个文本嵌入失败，记录但继续处理其他文本
                    self.logger.warning(f"文本嵌入失败，将跳过: {text[:50]}...")
            
            if len(embeddings) != len(texts):
                self.logger.warning(f"批量嵌入部分失败: {len(embeddings)}/{len(texts)} 成功")
                
            return embeddings if embeddings else None
        else:
            self.logger.error(f"不支持的嵌入模式: {self.mode}")
            return None

    def _local_embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        """使用本地模型批量嵌入文本"""
        if not self.model:
            self.logger.error("本地嵌入模型未初始化，无法嵌入文本")
            return None
            
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            self.logger.error(f"本地批量文本嵌入失败: {e}", exc_info=True)
            return None

# 单例获取函数
def get_embedding_service():
    try:
        service = EmbeddingService()
        return service
    except Exception as e:
        logger = LoggerManager().get_logger()
        logger.error(f"获取嵌入服务失败: {e}", exc_info=True)
        raise RuntimeError(f"无法初始化嵌入服务: {e}")