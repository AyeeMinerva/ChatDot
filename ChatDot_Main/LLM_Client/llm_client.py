import requests
import json


class LLMClient:
    """
    一个封装的 LLM 通信类，提供与 LLM 服务进行流式或非流式通信的功能。
    """

    def __init__(self, chat_url="http://127.0.0.1:11434/v1/chat/completions", model="gemma2:27b", max_tokens=10):
        """
        初始化 LLM 客户端。
        :param chat_url: LLM 服务的 URL
        :param model: 使用的模型名称
        :param max_tokens: 每次响应的最大 token 数
        """
        self.chat_url = chat_url
        self.model = model
        self.max_tokens = max_tokens
        self.messages = []  # 保存上下文消息

    def add_message(self, role, content):
        """
        向上下文中添加一条消息。
        :param role: 消息角色（如 'user', 'assistant', 'system'）
        :param content: 消息内容
        """
        self.messages.append({"role": role, "content": content})

    def clear_context(self):
        """清除上下文消息。"""
        self.messages = []

    def communicate(self, stream=True):
        """
        与 LLM 通信。
        :param stream: 是否使用流式输出
        :return: 如果 `stream` 为 True，则返回生成器；否则返回完整响应字符串
        """
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": self.messages
        }

        if stream:
            #流式模式
            data["stream"] = True
            try:
                with requests.post(self.chat_url, headers=headers, json=data, stream=True) as response:
                    response.raise_for_status()

                    # 返回生成器
                    for line in response.iter_lines():
                        if line:
                            chunk = line.decode("utf-8").strip()
                            # 检查并移除 data: 前缀
                            if chunk.startswith("data:"):
                                chunk = chunk[len("data:"):].strip()
                            if chunk == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(chunk)
                                content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"与 LLM 通信时发生错误: {e}")
            pass
        else:
            # 非流式模式
            try:
                response = requests.post(self.chat_url, headers=headers, json=data)
                response.raise_for_status()  # 如果状态码不是 2xx，则抛出异常

                result = response.json()

                # 验证响应结构并提取内容
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    if content:
                        yield content.strip()
                    else:
                        raise ValueError("非流式响应中未找到内容。")
                else:
                    raise ValueError("非流式响应结构无效，缺少 'choices' 字段。")
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"非流式请求失败：{e}")
            except (ValueError, KeyError) as e:
                raise RuntimeError(f"非流式响应解析失败：{e}")


    def get_last_messages(self):
        """返回当前上下文中的所有消息。"""
        return self.messages

#流式通信示例
# if __name__ == "__main__":
#     llm_client = LLMClient()

#     # 添加上下文消息
#     llm_client.add_message("system", "You are a helpful assistant.")
#     llm_client.add_message("user", "讲讲深度学习。")

#     try:
#         print("开始流式响应：")
#         for chunk in llm_client.communicate(stream=True):
#             print(chunk, end="", flush=True)
#     except RuntimeError as e:
#         print(e)

#非流式通信示例
# if __name__ == "__main__":
    
#     llm_client = LLMClient()

#     # 添加初始系统消息
#     llm_client.add_message("system", "You are a helpful assistant.")
#     llm_client.add_message("user", "给我介绍一下机器学习。")

#     try:
#         response = "".join(chunk for chunk in llm_client.communicate(stream=False))
#         print(f"非流式响应：{response}")
#     except RuntimeError as e:
#         print(e)
