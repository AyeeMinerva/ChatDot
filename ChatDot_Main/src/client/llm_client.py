import openai
from collections import deque
from threading import Lock

class LLMClient:
    """
    LLMClient 是一个管理与大型语言模型(LLM) API连接和通信的类。
    该类提供以下功能：
    - 通过轮询方式处理多个API密钥
    - 配置和测试API连接
    - 设置和管理模型参数
    - 处理与LLM的流式和非流式通信
    - 从API获取可用模型列表
    
    属性：
        client: OpenAI客户端实例
        api_keys (deque): 用于轮询的API密钥集合
        api_base (str): API的基础URL
        model_name (str): 要使用的LLM模型名称
        model_params (dict): 模型配置参数
        lock (Lock): 用于API密钥轮询的线程安全锁
    
    示例：
        ```
        client = LLMClient()
        client.set_api_config(['key1', 'key2'], 'https://api.base.url')
        client.set_model_name('gpt-3.5-turbo')
        response = client.communicate([{"role": "user", "content": "Hello"}])
        ```
    
    异常：
        ValueError: 当提供无效参数时
        RuntimeError: 当API连接失败或使用未初始化的客户端时
    """
    
    def __init__(self):
        self.client = None
        self.api_keys = deque()  # 使用双端队列存储多个API Keys
        self.api_base = None
        self.model_name = None
        self.model_params = {}
        self.lock = Lock()  # 用于线程安全的API Key轮询

    def set_api_config(self, api_keys, api_base, test_connection=True):
            """
            设置API配置
            @param api_keys: API密钥列表
            @param api_base: API基础URL
            @param test_connection: 是否测试连接，默认为True
            """
            if not api_keys or not api_base:
                raise ValueError("API Keys 和 API Base URL 不能为空。")
            if not isinstance(api_keys, list):
                raise ValueError("API Keys 必须是列表类型。")
            
            self.api_keys = deque(api_keys)
            self.api_base = api_base
            
            if test_connection:
                # 测试所有API Keys
                valid_keys = []
                for key in api_keys:
                    try:
                        test_client = openai.OpenAI(
                            api_key=key,
                            base_url=api_base
                        )
                        test_client.models.list()
                        valid_keys.append(key)
                    except Exception as e:
                        print(f"API Key {key[:8]}... 测试失败: {e}")
                
                #去除apikeys筛选逻辑
                # if not valid_keys:
                #     self.client = None
                #     raise RuntimeError("没有有效的API Keys")
                # self.api_keys = deque(valid_keys)
            
            # 不管是否测试，都设置第一个key为当前client
            self.client = openai.OpenAI(
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
            models = self.client.models.list()
            if not models:
                raise RuntimeError("无法获取模型列表，API 连接可能存在问题。")
            print("API 连接测试成功，成功获取模型列表...")
        except Exception as e:
            self.client = None
            raise RuntimeError(f"API 连接测试失败: {e}")

    def set_model_name(self, model_name):
        if not model_name:
            raise ValueError("模型名称不能为空。")
        self.model_name = model_name
        print(f"模型名称设置为: {model_name}")

    def get_model_name(self):
        return self.model_name

    def set_model_params(self, params):
        if not isinstance(params, dict):
            raise ValueError("模型参数必须是字典类型。")
        self.model_params = params
        print(f"模型参数设置为: {params}")

    def communicate(self, messages, model_name=None, stream=False, model_params_override=None):
        if not self.client:
            raise RuntimeError("LLMClient 未连接到 API，请先配置 API 连接。")

        final_model_name = model_name or self.model_name or "gpt-3.5-turbo"
        params = self.model_params.copy()
        if model_params_override:
            params.update(model_params_override)

        # 获取下一个API Key
        api_key = self.get_next_api_key()
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=self.api_base
        )

        print(f"--- LLM Request Parameters ---")
        print(f"Model Name: {final_model_name}")
        print(f"Model Params: {params}")
        print(f"Stream: {stream}")
        print(f"Messages: {messages}")

        try:
            response = self.client.chat.completions.create(
                model=final_model_name,
                messages=messages,
                stream=stream,
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
        if not self.client:
            raise RuntimeError("LLMClient 未连接到 API，请先配置 API 连接。")
        try:
            model_list = self.client.models.list()
            model_names = [model.id for model in model_list.data]
            return model_names
        except Exception as e:
            raise RuntimeError(f"获取模型列表失败: {e}")