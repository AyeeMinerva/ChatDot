import openai

class LLMClient:
    def __init__(self):
        self.client = None
        self.api_key = None
        self.api_base = None
        self.model_name = None #  !!!  新增模型名称属性 !!!
        self.model_params = {} #  !!!  新增模型参数字典 !!!


    def set_api_config(self, api_key, api_base):
        if not api_key or not api_base:
            raise ValueError("API Key 和 API Base URL 不能为空。")
        self.api_key = api_key
        self.api_base = api_base
        try:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            self.test_connection() #  !!!  连接成功后进行连接测试 !!!
        except Exception as e:
            self.client = None #  !!!  连接失败时 client 设置为 None !!!
            raise RuntimeError(f"API 连接失败: {e}")


    def test_connection(self): #  !!!  新增连接测试方法 !!!
        try:
            models = self.client.models.list() #  !!!  尝试获取模型列表 !!!
            if not models:
                raise RuntimeError("无法获取模型列表，API 连接可能存在问题。")
            print("API 连接测试成功，成功获取模型列表...") #  !!!  打印连接测试成功信息 !!!
        except Exception as e:
            self.client = None
            raise RuntimeError(f"API 连接测试失败: {e}")


    def set_model_name(self, model_name): #  !!!  新增 set_model_name 方法 !!!
        if not model_name:
            raise ValueError("模型名称不能为空。")
        self.model_name = model_name
        print(f"模型名称设置为: {model_name}") #  !!!  打印模型名称设置信息 !!!


    def get_model_name(self): #  !!!  新增 get_model_name 方法 !!!
        return self.model_name


    def set_model_params(self, params): #  !!!  新增 set_model_params 方法 !!!
        if not isinstance(params, dict):
            raise ValueError("模型参数必须是字典类型。")
        self.model_params = params
        print(f"模型参数设置为: {params}") #  !!!  打印模型参数设置信息 !!!


    def communicate(self, messages, model_name=None, stream=False, model_params_override=None):
        if not self.client:
            raise RuntimeError("LLMClient 未连接到 API，请先配置 API 连接。")

        final_model_name = model_name or self.model_name or "gpt-3.5-turbo" #  !!!  确定最终使用的模型名称 !!!
        params = self.model_params.copy() #  !!!  从 self.model_params 获取基础参数 !!!

        if model_params_override: #  !!!  如果有参数覆盖，则更新参数字典 !!!
            params.update(model_params_override)

        print(f"--- LLM Request Parameters ---") #  !!!  打印请求参数 !!!
        print(f"Model Name: {final_model_name}") #  !!!  打印模型名称 !!!
        print(f"Model Params: {params}") #  !!!  打印模型参数 !!!
        print(f"Stream: {stream}") #  !!!  打印是否流式输出 !!!
        print(f"Messages: {messages}") #  !!!  打印 messages 内容 !!!


        try:
            response = self.client.chat.completions.create(
                model=final_model_name,
                messages=messages,
                stream=stream,
                **params #  !!!  使用参数字典 !!!
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