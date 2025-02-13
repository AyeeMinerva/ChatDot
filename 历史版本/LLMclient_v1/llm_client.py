import openai
from openai import OpenAI
import os
import json  # 导入 json 模块，用于格式化输出

class LLMClient:
    """
    最终修正版的通用 LLM 客户端类。

    特点:
        - `__init__` 方法无参数，配置更加灵活，所有参数都通过方法调用或参数传递进行设置。
        - `communicate` 方法接收 `messages` 和 `model_name` 参数，方便动态指定对话内容和模型。
        - 解决了之前所有轮次中发现的错误，包括参数类型错误、上下文传递错误、模型名称传递错误等。
        - 代码包含详细的中文注释，方便理解和维护。

    使用方法:
        1. 创建 LLMClient 实例:  client = LLMClient()
        2. 配置 API 密钥和 Base URL: client.set_api_config(api_key="YOUR_API_KEY", api_base="YOUR_API_BASE_URL")
        3. (可选) 设置默认模型参数: client.default_model_params = {"temperature": 0.7, "top_p": 0.9}
        4. 与 LLM 进行对话:
           - 准备消息列表 messages, 例如:  messages = [{"role": "user", "content": "你好"}]
           - 调用 communicate 方法:  for chunk in client.communicate(messages=messages, model_name="gpt-3.5-turbo", stream=True): ...
    """
    def __init__(self): #  !!!  __init__ 方法不再接受任何参数 !!!
        """
        初始化 LLM 客户端。

        现在 __init__ 方法不再需要任何参数，API Key 和 API Base URL 需要稍后通过 set_api_config() 方法设置。
        模型名称、流式输出设置、默认模型参数等都可以在调用 communicate 方法时动态指定，或者使用默认值。
        """
        self.api_key = None
        self.api_base = None
        self.client = None # 初始时不创建 client 实例
        self.model_name = None # 默认模型名称设置为 None，表示需要动态指定
        self.stream = True # 默认启用流式输出，可以动态修改
        self.default_model_params = {} # 默认模型参数为空字典，可以动态设置

    def set_api_config(self, api_key, api_base):
        """
        设置 OpenAI API 的 API 密钥和 Base URL, 并创建 OpenAI 客户端实例。

        Args:
            api_key (str): OpenAI API 密钥。
            api_base (str): OpenAI API Base URL (例如: "https://api.openai.com/v1" 或 Gemini OpenAI 兼容层 Base URL)。

        Raises:
            ValueError: 如果 api_key 或 api_base 为空。
        """
        if not api_key or not api_base:
            raise ValueError("API Key 和 API Base URL 不能为空。")
        self.api_key = api_key
        self.api_base = api_base
        self.client = self._create_client()

    def _create_client(self):
        """
        创建 OpenAI 客户端实例。

        Returns:
            OpenAI: OpenAI 客户端实例。
        """
        return OpenAI(api_key=self.api_key, base_url=self.api_base)

    def fetch_available_models(self):
        """
        获取可用的模型列表。

        Returns:
            list: 模型名称列表。

        Raises:
            RuntimeError: 如果 API 客户端未配置 (未调用 set_api_config()) 或 API 调用失败。
        """
        if not self.client:
            raise RuntimeError("API 客户端未配置，请先调用 set_api_config()")
        try:
            model_list_response = self.client.models.list()
            return [model.id for model in model_list_response.data]
        except openai.APIError as e:
            raise RuntimeError(f"获取模型列表失败: {e}")

    def communicate(self, messages, model_name=None, stream=None, model_params_override=None):
        """
        与 LLM 进行通信，发送消息并获取 LLM 的响应。

        Args:
            messages (list): 对话消息列表，每个消息是一个字典，包含 "role" (角色，例如 "user", "assistant", "system") 和 "content" (消息内容)。
            model_name (str, optional): 要使用的模型名称。 如果指定，则覆盖 LLMClient 实例的默认模型名称。 默认为 None，表示使用默认模型名称。
            stream (bool, optional): 是否使用流式响应。 如果指定，则覆盖 LLMClient 实例的默认流式输出设置。 默认为 None，表示使用默认流式输出设置。
            model_params_override (dict, optional): 模型参数重载字典。 用于覆盖默认的模型参数。 默认为 None。

        Yields:
            str: 如果使用流式响应 (stream=True)，则以 chunk 的形式逐段返回 LLM 的响应文本。
            str: 如果不使用流式响应 (stream=False)，则一次性返回完整的 LLM 响应文本。

        Raises:
            RuntimeError: 如果 API 客户端未配置 (未调用 set_api_config()) 或 LLM API 通信失败。
            ValueError:  如果最终使用的模型名称为空 (既没有在 communicate 方法中指定，也没有在 LLMClient 初始化时设置默认模型名称)。
        """
        if not self.client:
            raise RuntimeError("API 客户端未配置，请先调用 set_api_config()")

        final_params = self.default_model_params.copy() # 复制默认模型参数
        if model_params_override:
            final_params.update(model_params_override) # 使用重载参数更新

        use_stream = stream if stream is not None else self.stream # 确定是否使用流式输出

        formatted_messages = messages  # 使用传入的消息列表

        # 确定最终使用的模型名称： 优先使用 communicate 方法传入的 model_name,  否则使用 self.model_name (初始化时设置的默认值)
        effective_model_name = model_name if model_name else self.model_name
        if not effective_model_name: # 如果最终模型名称仍然为空，则抛出错误
            raise ValueError("必须指定模型名称 (model_name)。")

        #  !!! 调试输出： 打印发送给 API 的 messages 参数 和 最终使用的模型名称 !!!
        print("\n--- Debug - Sending messages to API ---")
        print(json.dumps(formatted_messages, indent=2, ensure_ascii=False)) # 使用 json 格式化并输出，ensure_ascii=False 支持中文
        print(f"--- Debug - Using Model Name: {effective_model_name} ---") #  调试输出最终使用的模型名称
        print("--- Debug End ---\n")

        try:
            if use_stream:
                response_stream = self.client.chat.completions.create(
                    model=effective_model_name, # 使用最终确定的模型名称
                    messages=formatted_messages, # 使用传递进来的 messages
                    stream=True,
                    **final_params # 直接传递模型参数
                )
                return self._process_stream_response(response_stream)
            else:
                response = self.client.chat.completions.create(
                    model=effective_model_name, # 使用最终确定的模型名称
                    messages=formatted_messages, # 使用传递进来的 messages
                    stream=False,
                    **final_params # 直接传递模型参数
                )
                return self._process_non_stream_response(response)
        except openai.APIError as e:
            raise RuntimeError(f"LLM API 通信错误: {e}")

    def _process_stream_response(self, response_stream):
        """
        处理流式响应，逐段生成响应文本。

        Args:
            response_stream (openai.Stream): OpenAI API 返回的流式响应对象。

        Yields:
            str: LLM 响应的文本 chunk。
        """
        for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content: # 增加防御性检查
                chunk_message = chunk.choices[0].delta.content or ""
                if chunk_message:
                    yield chunk_message

    def _process_non_stream_response(self, response):
        """
        处理非流式响应，一次性获取完整响应文本。

        Args:
            response (openai.ChatCompletion): OpenAI API 返回的非流式响应对象。

        Returns:
            str: 完整的 LLM 响应文本。
        """
        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    # 示例测试代码 (请根据您的 API 配置修改)
    openai_client = LLMClient( ) #  !!!  创建 LLMClient 实例时不再需要模型名称 !!!
    openai_client.model_name = "gpt-3.5-turbo" #  !!!  需要手动设置默认模型名称，或者在 communicate 方法中指定 !!!
    openai_client.stream = True #  !!!  可以手动设置 stream 或使用默认值 True !!!


    api_base_url = "https://api.openai.com/v1"  #  标准的 OpenAI API Base URL
    api_key_value = "YOUR_OPENAI_API_KEY" #  !!!  请替换为您的 OpenAI API Key  !!!

    try:
        openai_client.set_api_config(api_key=api_key_value, api_base=api_base_url)

        models = openai_client.fetch_available_models()
        print("可用模型列表:")
        for model_name in models:
            print(f"- {model_name}")

        #  !!!  示例代码需要修改，因为 LLMClient 不再维护 messages 列表，需要手动创建和传递 !!!
        messages = [{"role": "user", "content": "请用中文简要介绍一下你自己。"}] #  手动创建消息列表
        print("\n开始流式响应 (OpenAI - gpt-3.5-turbo):")
        for chunk in openai_client.communicate(messages=messages, model_name="gpt-3.5-turbo"): #  !!!  将消息列表和模型名称传递给 communicate 方法  !!!
            print(chunk, end="", flush=True)

    except RuntimeError as e:
        print(f"\nError: {e}")
    except ValueError as e:
        print(f"\nAPI 配置错误: {e}")