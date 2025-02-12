import openai
from openai import OpenAI  # 明确导入 OpenAI 类
import os  # 导入 os 模块，用于处理环境变量

class LLMClient:
    """
    通用 LLM 客户端类，使用 OpenAI SDK，旨在兼容多种 OpenAI 兼容的 LLM API。
    提供流式和非流式通信，支持模型参数条件性调整，并新增动态获取模型列表的功能。
    API 类型由 OpenAI SDK 基于 api_base 隐式处理，无需显式指定 api_type 参数。

    **重要更新：**
        - **延迟 API 配置：**  现在 `LLMClient` 可以在初始化时无需提供 API Key 和 API Base URL。
          API 配置 (api_key, api_base) 可以稍后通过 `set_api_config()` 方法设置。
        - **`set_api_config()` 方法：**  新增 `set_api_config(api_key, api_base)` 方法，用于设置 API 密钥和 Base URL，
          并在配置完成后创建 OpenAI 客户端实例。
        - **默认构造函数修改：**  默认构造函数不再需要 `api_key` 和 `api_base` 参数。

    **编码注意事项：**
    ... (之前的编码注意事项保持不变) ...

    核心功能：
        - ... (之前的核心功能描述保持不变) ...
    """

    def __init__(self, model_name="gpt-3.5-turbo", stream=True, **default_model_params):
        """
        初始化 LLM 客户端。 **默认构造函数不再需要 API Key 和 API Base URL。**
        API Key 和 API Base URL 需要稍后通过 `set_api_config()` 方法设置。

        :param model_name: 使用的模型名称 (API 中使用的模型标识符)。 ... (之前的参数描述保持不变) ...
        :param stream: 是否默认使用流式输出。 ... (之前的参数描述保持不变) ...
        :param default_model_params: 默认的模型参数字典。 ... (之前的参数描述保持不变) ...
        """
        # 移除 api_key 和 api_base 参数，默认设置为 None
        self.api_key = None
        self.api_base = None
        self.model_name = model_name
        self.stream = stream
        self.default_model_params = default_model_params
        self.messages = []
        self.client = None # 初始时不创建 client 实例，延迟到 set_api_config()

    def set_api_config(self, api_key, api_base):
        """
        设置 API 密钥和 Base URL，并创建 OpenAI 客户端实例。
        **必须在调用 `communicate()` 或 `fetch_available_models()` 等 API 方法之前调用此方法。**

        :param api_key: API 密钥。
        :param api_base: API Base URL。
        :raises ValueError: 如果 api_key 或 api_base 为空。
        """
        if not api_key or not api_base:
            raise ValueError("API Key 和 API Base URL 不能为空。")  # 抛出 ValueError 异常，提示配置不完整
        self.api_key = api_key
        self.api_base = api_base
        self.client = self._create_client() # 配置完成后，创建 client 实例


    def _create_client(self):
        """
        根据当前的 API 配置 (api_base) 创建 OpenAI 客户端实例。
        API 类型 (OpenAI, Azure, Ollama, DeepSeek 等) 由 OpenAI SDK 自动处理。
        """
        if self.api_base:
            # 显式使用 UTF-8 编码处理 api_key 和 api_base (虽然 OpenAI SDK 内部应该已经处理)
            api_key_encoded = self.api_key.encode('utf-8').decode('utf-8') if self.api_key else "任意字符串，Ollama 等可能需要"
            api_base_encoded = self.api_base.encode('utf-8').decode('utf-8') if self.api_base else None

            return OpenAI(api_key=api_key_encoded, base_url=api_base_encoded)
        else:
            api_key_encoded = self.api_key.encode('utf-8').decode('utf-8') if self.api_key else None
            return OpenAI(api_key=api_key_encoded)

    def add_message(self, role, content):
        """添加消息到上下文。"""
        self.messages.append({"role": role, "content": content})

    def clear_context(self):
        """清除上下文消息。"""
        self.messages = []

    def communicate(self, stream=None, user_messages=None, model_params_override=None):
        """与 LLM 进行通信。"""
        if not self.client: # 检查 client 实例是否已创建
            raise RuntimeError("API 客户端未配置。请先调用 `set_api_config()` 方法设置 API Key 和 Base URL。")

        final_model_params = {}
        default_params = self.default_model_params
        if default_params:
             final_model_params.update(default_params)
        if model_params_override:
            final_model_params.update(model_params_override)

        params_to_send = {k: v for k, v in final_model_params.items() if v is not None}

        use_stream = stream if stream is not None else self.stream

        try:
            if use_stream:
                response_stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=user_messages or self.messages,
                    stream=True,
                    **params_to_send
                )
                return self._process_stream_response(response_stream)
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=user_messages or self.messages,
                    stream=False,
                    **params_to_send
                )
                return self._process_non_stream_response(response)
        except openai.APIError as e:
            raise RuntimeError(f"与 LLM API 通信时发生错误: {e}")

    def _process_stream_response(self, response_stream):
        """处理流式响应。"""
        try:
            for chunk in response_stream:
                chunk_message = chunk.choices[0].delta.content or ""
                if chunk_message:
                    yield chunk_message
        except Exception as e:
             raise RuntimeError(f"处理流式响应时发生错误: {e}")

    def _process_non_stream_response(self, response):
        """处理非流式响应。"""
        try:
            return response.choices[0].message.content.strip()
        except (AttributeError, KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"处理非流式响应时发生错误: {e}")

    def get_last_messages(self):
        """返回上下文消息列表。"""
        return self.messages

    def fetch_available_models(self):
        """
        调用 OpenAI SDK 接口，从 API 服务获取可用的模型列表。
        **请确保在调用此方法之前已通过 `set_api_config()` 配置 API 客户端。**

        :return: 包含可用模型名称的列表 (字符串列表)。
        :raises RuntimeError: 如果获取模型列表的过程中发生任何 API 错误或异常，
                             或者 API 客户端尚未配置。
        """
        if not self.client: # 检查 client 实例是否已创建
            raise RuntimeError("API 客户端未配置。请先调用 `set_api_config()` 方法设置 API Key 和 Base URL。")
        try:
            model_list_response = self.client.models.list() # 调用 OpenAI SDK 的 models.list() 方法获取模型列表
            model_names = [model.id for model in model_list_response.data] # 从响应数据中提取模型名称 (model.id)
            return model_names # 返回模型名称列表
        except openai.APIError as e: # 捕获 OpenAI SDK 抛出的 APIError 异常
            raise RuntimeError(f"获取模型列表失败: {e}") # 转换为 RuntimeError 异常并抛出


# 示例代码 (可以移除或保留):
if __name__ == "__main__":
    # 初始化 LLMClient，不带 API 配置
    ollama_client = LLMClient(
        model_name="llama2",
        stream=True,
        default_model_params={
            "temperature": 0.8,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
    )

    #  稍后设置 API 配置 (例如，从用户输入或配置文件中获取)
    api_base_url = "http://localhost:11434/v1"  #  替换为您的 API Base URL
    api_key_value = None #  替换为您的 API Key，如果需要

    try:
        ollama_client.set_api_config(api_key=api_key_value, api_base=api_base_url) # 设置 API 配置

        # 测试获取模型列表功能
        test_client = ollama_client #  或者 openai_client, deepseek_client, azure_client
        models = test_client.fetch_available_models()
        print("可用模型列表:")
        for model_name in models:
            print(f"- {model_name}")

        test_client = ollama_client # 选择要测试的客户端
        test_client.add_message("user", "请用中文简要介绍一下你自己, 并且以列表形式列出你的主要功能。")

        print("\n开始流式响应：")
        for chunk in test_client.communicate():
            print(chunk, end="", flush=True)

    except RuntimeError as e:
        print(f"\nError: {e}")
    except ValueError as e: # 捕获 ValueError 异常，处理 API 配置错误
        print(f"\nAPI 配置错误: {e}")