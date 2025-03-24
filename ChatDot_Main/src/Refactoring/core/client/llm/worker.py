import threading

class LLMWorker(threading.Thread):
    """
    LLMWorker 用于异步处理与 LLM 的通信任务。
    支持流式输出和非流式输出。
    """
    def __init__(self, llm_client, messages, model_name=None, model_params_override=None, 
                 on_complete=None, on_error=None, on_stream=None):
        """
        初始化 LLMWorker。
        :param llm_client: LLMClient 实例
        :param messages: 要发送的消息列表
        :param model_name: 使用的模型名称
        :param model_params_override: 模型参数覆盖
        :param on_complete: 任务完成时的回调函数
        :param on_error: 任务出错时的回调函数
        :param on_stream: 流式输出时的回调函数
        """
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.model_name = model_name
        self.model_params_override = model_params_override
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_stream = on_stream

    def run(self):
        try:
            response = self.llm_client.communicate(
                messages=self.messages,
                model_name=self.model_name,
                model_params_override=self.model_params_override
            )
            if callable(response):  # 如果是流式输出
                for chunk in response():
                    if self.on_stream:
                        self.on_stream(chunk)
            else:  # 非流式输出
                if self.on_complete:
                    self.on_complete(response)
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))