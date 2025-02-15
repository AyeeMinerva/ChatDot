from PyQt5.QtCore import QThread, pyqtSignal

class LLMChatThread(QThread):
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
            for chunk in self.llm_client.communicate(messages=self.messages, model_name=self.model_name, stream=True, model_params_override=self.model_params_override):
                if not self._is_running:
                    break
                self.stream_output.emit(chunk)
        except RuntimeError as e:
            self.stream_output.emit(f"\n[Error]: {e}")
        finally:
            self.complete.emit()

    def stop(self):
        self._is_running = False

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