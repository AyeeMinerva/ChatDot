import warnings
import openai
from collections import deque
from threading import Lock
from global_managers.logger_manager import LoggerManager

class LLMAdapter:
    """
    LLMAdapter 是一个管理与大型语言模型(LLM) API连接和通信的类。
    该类提供以下功能：
    - 通过轮询方式处理多个API密钥
    - 配置和测试API连接
    - 设置和管理模型参数
    - 处理与LLM的流式和非流式通信
    - 从API获取可用模型列表
    
    属性：
        adapter: OpenAI客户端实例
        api_keys (deque): 用于轮询的API密钥集合
        api_base (str): API的基础URL
        model_name (str): 要使用的LLM模型名称
        model_params (dict): 模型配置参数
        lock (Lock): 用于API密钥轮询的线程安全锁
    
    示例：
        ```
        adapter = LLMAdapter()
        adapter.set_api_config(['key1', 'key2'], 'https://api.base.url')
        adapter.set_model_name('gpt-3.5-turbo')
        response = adapter.communicate([{"role": "user", "content": "Hello"}])
        ```
    
    异常：
        ValueError: 当提供无效参数时
        RuntimeError: 当API连接失败或使用未初始化的客户端时
    """
    
    def __init__(self):
        self.adapter = None
        self.api_keys = deque()  # 使用双端队列存储多个API Keys
        self.api_base = None
        self.model_name = None
        self.model_params = {}
        self.lock = Lock()  # 用于线程安全的API Key轮询

    def set_api_config(self, api_keys, api_base, test_connection=False):
        """
        设置API配置
        @param api_keys: API密钥列表
        @param api_base: API基础URL
        @param test_connection: 是否测试连接，默认为False
        """
        # 检查并发出警告
        if not api_keys or not api_base:
            warnings.warn("API Keys 或 API Base URL 为空，将使用默认OpenAI配置。注意：需要设置有效的API密钥才能正常使用。")
            api_keys = api_keys or [""]  # 使用空字符串作为默认key
            api_base = api_base or "https://api.openai.com/v1"

        # 确保api_keys是列表类型
        if not isinstance(api_keys, list):
            warnings.warn("API Keys 不是列表类型，已自动转换为列表。")
            api_keys = [api_keys]
            
        self.api_keys = deque(api_keys)
        self.api_base = api_base
            
        if test_connection:
            # 测试所有API Keys
            valid_keys = []
            for key in api_keys:
                try:
                    test_adapter = openai.OpenAI(
                        api_key=key,
                        base_url=api_base
                    )
                    test_adapter.models.list()
                    valid_keys.append(key)
                except Exception as e:
                    LoggerManager().get_logger().warning(f"API Key {key[:8]}... 测试失败(llm_adapter.set_api_config): {e}")
            
            #去除apikeys筛选逻辑
            # if not valid_keys:
            #     self.adapter = None
            #     raise RuntimeError("没有有效的API Keys")
            # self.api_keys = deque(valid_keys)
        
        # 不管是否测试，都设置第一个key为当前adapter
        self.adapter = openai.OpenAI(
            api_key=self.api_keys[0],
            base_url=api_base
        )
        
    def get_next_api_key(self):
        with self.lock:
            current_key = self.api_keys[0]
            self.api_keys.rotate(-1)  # 轮询调度
            return current_key

    def test_connection(self):
        try:
            models = self.adapter.models.list()
            if not models:
                raise RuntimeError("无法获取模型列表，API 连接可能存在问题。")
            LoggerManager().get_logger().debug("API 连接测试成功，成功获取模型列表...")
        except Exception as e:
            self.adapter = None
            raise RuntimeError(f"API 连接测试失败(test_connection): {e}")

    def set_model_name(self, model_name):
        if not model_name:
            raise ValueError("模型名称不能为空。")
        self.model_name = model_name
        LoggerManager().get_logger().debug(f"模型名称设置为: {model_name}")

    def get_model_name(self):
        return self.model_name

    def set_model_params(self, params):
        if not isinstance(params, dict):
            raise ValueError("模型参数必须是字典类型。")
        self.model_params = params
        LoggerManager().get_logger().debug(f"模型参数设置为: {params}")
        if 'stream' not in self.model_params:
            self.model_params['stream'] = True  # 默认启用
    
    def stop_generating(self):
        """
        尝试停止当前生成过程
        
        Returns:
            bool: 如果成功执行API级打断则返回True，否则返回False
        """
        try:
            if hasattr(self, '_current_response') and self._current_response:
                if hasattr(self._current_response, 'abort'):
                    self._current_response.abort()
                    LoggerManager().get_logger().debug("LLM API 级打断成功")
                    return True
                else:
                    LoggerManager().get_logger().debug("当前 LLM API 不支持打断操作")
        except Exception as e:
            LoggerManager().get_logger().warning(f"LLM API 级打断失败: {e}")
        return False
    
    #def communicate(self, messages, model_name=None, stream=False, model_params_override=None): #stream参数现已整合进params
    def communicate(self, messages, model_name=None, model_params_override=None):
        if not self.adapter:
            raise RuntimeError("LLMAdapter 未连接到 API，请先配置 API 连接。")

        final_model_name = model_name or self.model_name or "gpt-3.5-turbo"
        params = self.model_params.copy()
        if model_params_override:
            params.update(model_params_override)

        # 获取下一个API Key
        api_key = self.get_next_api_key()
        self.adapter = openai.OpenAI(
            api_key=api_key,
            base_url=self.api_base
        )
        stream = params.get('stream', False)
        LoggerManager().get_logger().debug(f"--- LLM Request Parameters ---")
        LoggerManager().get_logger().debug(f"Bae URL: {self.api_base}")
        LoggerManager().get_logger().debug(f"API Key: {api_key}")
        LoggerManager().get_logger().debug(f"Model Name: {final_model_name}")
        LoggerManager().get_logger().debug(f"Model Params: {params}")
        #LoggerManager().get_logger().debug(f"Stream: {stream}") #stream参数现已整合进params
        LoggerManager().get_logger().debug(f"Messages: {messages}")
        LoggerManager().get_logger().debug("-------------------------------")

        try:
            response = self.adapter.chat.completions.create(
                model=final_model_name,
                messages=messages,
                #stream=stream, #stream参数现已整合进params
                **params
            )
            if stream:
                def chunk_generator():
                    for chunk in response:
                        chunk_content = chunk.choices[0].delta.content or ""
                        yield chunk_content
                return chunk_generator()
            else:
                return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM 通信失败: {e}")

    def fetch_available_models(self):
        if not self.adapter:
            raise RuntimeError("LLMAdapter 未连接到 API，请先配置 API 连接。")
        try:
            model_list = self.adapter.models.list()
            model_names = [model.id for model in model_list.data]
            return model_names
        except Exception as e:
            raise RuntimeError(f"获取模型列表失败: {e} (url: {self.api_base})")