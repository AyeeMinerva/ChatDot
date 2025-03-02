from PyQt5.QtCore import QThread, pyqtSignal

class LLMChatThread(QThread):
    """
    LLMChatThread类用于处理与大语言模型(LLM)的异步聊天交互。
    该类继承自QThread，实现了与LLM的流式通信功能。通过QThread的方式运行可以避免在通信过程中阻塞主界面。
    Signals:
        stream_output (str): 用于发送LLM返回的流式输出文本
        complete: 在通信完成时发出信号
    Attributes:
        llm_client: LLM客户端实例
        messages (list): 对话消息列表
        model_params_override (dict): 模型参数覆盖设置
        model_name (str): 使用的模型名称
        _is_running (bool): 控制线程运行状态的标志
    Methods:
        run(): 执行LLM通信的主要逻辑
        stop(): 停止当前运行的通信线程
    """
    stream_output = pyqtSignal(str)
    complete = pyqtSignal()

    def __init__(self, llm_client, messages, model_params_override, model_name):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.model_params_override = model_params_override
        self.model_name = model_name
        self._is_running = True  # 新增标志

    def run(self):
        self._is_running = True
        try:
            # 检查是否使用流式输出
            use_stream = self.model_params_override.get('stream', True)
            
            if use_stream:
                # 流式输出模式
                for chunk in self.llm_client.communicate(
                    messages=self.messages,
                    model_name=self.model_name, 
                    model_params_override=self.model_params_override
                ):
                    if not self._is_running:
                        break
                    self.stream_output.emit(chunk)
            else:
                # 非流式输出模式
                response = self.llm_client.communicate(
                    messages=self.messages,
                    model_name=self.model_name,
                    model_params_override=self.model_params_override
                )
                if self._is_running:
                    self.stream_output.emit(response)
                    
        except RuntimeError as e:
            self.stream_output.emit(f"\n[Error]: {e}")
        finally:
            self.complete.emit()

    def stop(self):
        self._is_running = False
        self.terminate()
        self.wait()

class LLMModelListThread(QThread):
    models_fetched = pyqtSignal(list)
    error_fetching_models = pyqtSignal(str)

    def __init__(self, llm_client):
        super().__init__()
        self.llm_client = llm_client

    def run(self):
        try:
            model_names = self.llm_client.fetch_available_models()
            self.models_fetched.emit(model_names)
        except RuntimeError as e:
            self.error_fetching_models.emit(str(e))