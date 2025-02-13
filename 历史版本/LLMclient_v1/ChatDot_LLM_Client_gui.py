import os
os.environ['PYTHONIOENCODING'] = 'UTF-8' # 设置 PythonIOENCODING 环境变量为 UTF-8，避免控制台输出中文乱码

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QTextEdit, QLineEdit,
                             QWidget, QPushButton, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
                             QSpinBox, QCheckBox, QScrollArea, QGridLayout, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QThread, pyqtSignal

from llm_client import LLMClient # 导入 LLMClient 类

class LLMChatThread(QThread):
    """
    LLM 聊天线程类，用于在后台线程中进行 LLM API 调用，避免阻塞 UI 线程。

    信号:
        stream_output (pyqtSignal(str)): 流式输出信号，用于逐段发送 LLM 响应文本到 UI 线程。
        complete (pyqtSignal): 完成信号，用于通知 UI 线程 LLM 响应已完成。
    """
    stream_output = pyqtSignal(str) # 流式输出信号
    complete = pyqtSignal() # 完成信号

    def __init__(self, llm_client, messages, model_params_override, model_name):
        """
        初始化 LLMChatThread 线程。

        Args:
            llm_client (LLMClient): LLM 客户端实例，用于进行 API 调用。
            messages (list): 对话消息列表，传递给 LLMClient.communicate 方法。
            model_params_override (dict): 模型参数重载字典，传递给 LLMClient.communicate 方法。
            model_name (str): 要使用的模型名称，传递给 LLMClient.communicate 方法。
        """
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.model_params_override = model_params_override
        self.model_name = model_name # 模型名称

    def run(self):
        """
        线程运行函数，在后台线程中调用 LLMClient.communicate 方法进行 API 调用，并通过信号发送响应。
        """
        try:
            # 调用 LLMClient 的 communicate 方法进行 API 通信，并将 messages, model_name, stream, model_params_override 参数传递给它
            for chunk in self.llm_client.communicate(messages=self.messages, model_name=self.model_name, stream=True, model_params_override=self.model_params_override):
                self.stream_output.emit(chunk) # 通过 stream_output 信号逐段发送 LLM 响应文本到 UI 线程
        except RuntimeError as e:
            self.stream_output.emit(f"\n[Error]: {e}") # 通过 stream_output 信号发送错误信息到 UI 线程
        finally:
            self.complete.emit() # 发送 complete 信号，通知 UI 线程 LLM 响应已完成

class LLMModelListThread(QThread):
    """
    LLM 模型列表获取线程类，用于在后台线程中获取可用模型列表，避免阻塞 UI 线程。

    信号:
        models_fetched (pyqtSignal(list)): 模型列表获取成功信号，用于发送模型名称列表到 UI 线程。
        error_fetching_models (pyqtSignal(str)): 模型列表获取失败信号，用于发送错误信息到 UI 线程。
    """
    models_fetched = pyqtSignal(list) # 模型列表获取成功信号
    error_fetching_models = pyqtSignal(str) # 模型列表获取失败信号

    def __init__(self, llm_client):
        """
        初始化 LLMModelListThread 线程。

        Args:
            llm_client (LLMClient): LLM 客户端实例，用于获取模型列表。
        """
        super().__init__()
        self.llm_client = llm_client

    def run(self):
        """
        线程运行函数，在后台线程中调用 LLMClient.fetch_available_models 方法获取模型列表，并通过信号发送结果。
        """
        try:
            model_names = self.llm_client.fetch_available_models() # 调用 LLMClient 的 fetch_available_models 方法获取模型列表
            self.models_fetched.emit(model_names) # 通过 models_fetched 信号发送模型名称列表到 UI 线程
        except RuntimeError as e:
            self.error_fetching_models.emit(str(e)) # 通过 error_fetching_models 信号发送错误信息到 UI 线程


class ChatWindow(QMainWindow):
    """
    PyQt5 聊天窗口主类，负责构建用户界面，处理用户输入，与 LLMClient 交互，显示 LLM 响应。
    """
    def __init__(self):
        """
        初始化 ChatWindow 窗口。
        """
        super().__init__()
        self.setWindowTitle("简洁 LLM 聊天窗口 (重写版)") # 设置窗口标题

        self.llm_client = LLMClient()  # 创建 LLMClient 实例，用于与 LLM API 交互，注意这里创建 LLMClient 时不再需要模型名称参数
        self.llm_thread = None # LLM 聊天线程
        self.model_list_thread = None # 模型列表获取线程

        self.messages = [{"role": "system", "content": "You are a helpful assistant."}] # 初始化对话消息列表，包含默认的系统消息
        self.param_checkboxes = {} # 模型参数复选框字典，用于存储参数复选框
        self.assistant_prefix_added = False #  !!!  新增实例变量，用于标记是否已添加 "助手: " 前缀  !!!

        self.init_ui() # 初始化用户界面

    def init_ui(self):
        """
        初始化用户界面，包括创建和布局各种 UI 元素。
        """
        self.central_widget = QWidget(self) # 创建中心 Widget
        self.setCentralWidget(self.central_widget) # 设置中心 Widget
        self.layout = QVBoxLayout(self.central_widget) # 创建垂直布局

        # 1. 聊天显示区域
        self.chat_display = QTextEdit(self) # 创建 QTextEdit 用于显示聊天记录
        self.chat_display.setReadOnly(True) # 设置为只读
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # 设置尺寸策略
        self.layout.addWidget(self.chat_display) # 添加到布局

        # 2. 用户输入区域
        self.user_input_layout = QHBoxLayout() # 创建水平布局
        self.user_input = QLineEdit(self) # 创建 QLineEdit 用于用户输入
        self.user_input.setPlaceholderText("请输入消息...") # 设置占位符文本
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # 设置尺寸策略
        self.user_input.returnPressed.connect(self.send_message) # 连接回车键信号到 send_message 方法
        self.user_input_layout.addWidget(self.user_input) # 添加到布局

        self.send_button = QPushButton("发送", self) # 创建 "发送" 按钮
        self.send_button.clicked.connect(self.send_message) # 连接点击信号到 send_message 方法
        self.send_button.setEnabled(False) # 初始禁用，等待 API 连接成功后启用
        self.user_input_layout.addWidget(self.send_button) # 添加到布局
        self.layout.addLayout(self.user_input_layout) # 添加用户输入区域布局到主布局

        # 3.  参数配置和操作按钮区域 (滚动区域)
        self.params_scroll_area = QScrollArea(self) # 创建滚动区域
        self.params_widget = QWidget() # 创建 Widget 用于容纳参数配置和操作按钮
        self.params_layout = QGridLayout(self.params_widget) # 创建网格布局
        self.params_scroll_area.setWidgetResizable(True) # 允许内部 widget 调整大小
        self.params_scroll_area.setWidget(self.params_widget) # 设置滚动区域的内部 widget
        self.layout.addWidget(self.params_scroll_area) # 添加滚动区域到主布局

        row = 0 # 网格布局行索引

        # API 配置区域
        self.api_base_label = QLabel("API Base URL:", self) # 创建 API Base URL 标签
        self.api_base_input = QLineEdit(self) # 创建 API Base URL 输入框
        self.params_layout.addWidget(self.api_base_label, row, 0) # 添加到网格布局
        self.params_layout.addWidget(self.api_base_input, row, 1, 1, 2) # 添加到网格布局，跨 2 列
        row += 1

        self.api_key_label = QLabel("API Key:", self) # 创建 API Key 标签
        self.api_key_input = QLineEdit(self) # 创建 API Key 输入框
        self.params_layout.addWidget(self.api_key_label, row, 0) # 添加到网格布局
        self.params_layout.addWidget(self.api_key_input, row, 1, 1, 2) # 添加到网格布局，跨 2 列
        row += 1

        self.connect_button = QPushButton("连接", self) # 创建 "连接" 按钮
        self.connect_button.clicked.connect(self.connect_api) # 连接点击信号到 connect_api 方法
        self.params_layout.addWidget(self.connect_button, row, 1) # 添加到网格布局
        row += 1

        # 模型选择区域
        self.model_name_label = QLabel("模型:", self) # 创建 "模型" 标签
        self.model_name_combo = QComboBox(self) # 创建模型下拉框
        self.model_name_combo.addItem("请先连接API") # 添加初始提示项
        self.model_name_combo.setEnabled(False) # 初始禁用，等待 API 连接成功后启用
        self.params_layout.addWidget(self.model_name_label, row, 0) # 添加到网格布局
        self.params_layout.addWidget(self.model_name_combo, row, 1, 1, 2) # 添加到网格布局，跨 2 列
        row += 1

        # 模型参数调整区域
        self.temp_spinbox = QDoubleSpinBox(self, minimum=0.0, maximum=2.0, singleStep=0.1, value=0.7) # 创建 temperature 参数调节 SpinBox
        row = self.add_parameter_row("temperature", "温度:", self.temp_spinbox, row) # 添加参数行
        self.top_p_spinbox = QDoubleSpinBox(self, minimum=0.0, maximum=1.0, singleStep=0.05, value=0.9) # 创建 top_p 参数调节 SpinBox
        row = self.add_parameter_row("top_p", "Top P:", self.top_p_spinbox, row) # 添加参数行
        self.max_tokens_spinbox = QSpinBox(self, minimum=1, maximum=4096, singleStep=100, value=200) # 创建 max_tokens 参数调节 SpinBox
        row = self.add_parameter_row("max_tokens", "最大 Token:", self.max_tokens_spinbox, row) # 添加参数行
        self.frequency_penalty_spinbox = QDoubleSpinBox(self, minimum=-2.0, maximum=2.0, singleStep=0.1, value=0.0) # 创建 frequency_penalty 参数调节 SpinBox
        row = self.add_parameter_row("frequency_penalty", "频率惩罚:", self.frequency_penalty_spinbox, row) # 添加参数行
        self.presence_penalty_spinbox = QDoubleSpinBox(self, minimum=-2.0, maximum=2.0, singleStep=0.1, value=0.0) # 创建 presence_penalty 参数调节 SpinBox
        row = self.add_parameter_row("presence_penalty", "存在惩罚:", self.presence_penalty_spinbox, row) # 添加参数行

        self.stream_checkbox = QCheckBox("流式输出", self) # 创建 "流式输出" 复选框
        self.stream_checkbox.setChecked(True) # 默认启用流式输出
        self.params_layout.addWidget(self.stream_checkbox, row, 0, 1, 3) # 添加到网格布局，跨 3 列
        row += 1

        # 操作按钮区域
        self.operation_layout = QHBoxLayout() # 创建水平布局
        self.stop_button = QPushButton("停止", self) # 创建 "停止" 按钮
        self.stop_button.clicked.connect(self.stop_llm) # 连接点击信号到 stop_llm 方法
        self.stop_button.setEnabled(False) # 初始禁用，等待 API 连接成功后启用
        self.operation_layout.addWidget(self.stop_button) # 添加到布局

        self.clear_button = QPushButton("清除上下文", self) # 创建 "清除上下文" 按钮
        self.clear_button.clicked.connect(self.clear_context) # 连接点击信号到 clear_context 方法
        self.clear_button.setEnabled(False) # 初始禁用，等待 API 连接成功后启用
        self.operation_layout.addWidget(self.clear_button) # 添加到布局
        self.params_layout.addLayout(self.operation_layout, row, 0, 1, 3) # 将操作按钮布局添加到参数配置区域网格布局，跨 3 列
        row += 1

        self.setLayout(self.layout) # 设置窗口主布局 (注意: 这里只需要设置一次主布局，之前可能重复设置了)


    def add_parameter_row(self, param_name, label_text, control, row_index):
        """
        添加模型参数行到参数配置区域网格布局中。

        Args:
            param_name (str): 参数名称，用于标识参数。
            label_text (str): 参数标签文本，显示在 UI 上。
            control (QWidget): 参数调节 UI 控件 (例如 QDoubleSpinBox, QSpinBox)。
            row_index (int): 参数行在网格布局中的行索引。

        Returns:
            int: 下一行在网格布局中的行索引。
        """
        label = QLabel(label_text, self) # 创建参数标签
        checkbox = QCheckBox(self) # 创建参数启用复选框
        checkbox.setChecked(False) # 默认不启用
        self.param_checkboxes[param_name] = checkbox # 将复选框添加到参数复选框字典中

        self.params_layout.addWidget(label, row_index, 0) # 标签添加到网格布局
        self.params_layout.addWidget(control, row_index, 1) # 控件添加到网格布局
        self.params_layout.addWidget(checkbox, row_index, 2) # 复选框添加到网格布局
        return row_index + 1 # 返回下一行索引


    def connect_api(self):
        """
        连接 API，配置 LLMClient 实例，并获取可用模型列表。
        """
        api_key = self.api_key_input.text().strip() # 获取用户输入的 API Key
        api_base = self.api_base_input.text().strip() # 获取用户输入的 API Base URL

        try:
            self.llm_client.set_api_config(api_key=api_key, api_base=api_base) # 调用 LLMClient 的 set_api_config 方法配置 API
            self.chat_display.append("API 连接成功 (标准 OpenAI 格式)...") # 在聊天显示区域显示连接成功消息
            self.get_model_list() # 连接成功后获取模型列表
            self.send_button.setEnabled(True) # 连接成功后启用 "发送" 按钮
            self.stop_button.setEnabled(True) # 连接成功后启用 "停止" 按钮
            self.clear_button.setEnabled(True) # 连接成功后启用 "清除上下文" 按钮
        except ValueError as e:
            QMessageBox.warning(self, "API 配置错误", str(e)) # 弹出警告对话框显示 API 配置错误信息
            self.chat_display.append(f"[Error] API 配置错误: {e}") # 在聊天显示区域显示 API 配置错误信息
            self.model_name_combo.clear() # 清空模型下拉框
            self.model_name_combo.addItem("API 配置错误") # 添加 "API 配置错误" 提示项
            self.model_name_combo.setEnabled(False) # 禁用模型下拉框
            self.send_button.setEnabled(False) # 禁用 "发送" 按钮
            self.stop_button.setEnabled(False) # 禁用 "停止" 按钮
            self.clear_button.setEnabled(False) # 禁用 "清除上下文" 按钮
        except RuntimeError as e:
            QMessageBox.critical(self, "API 连接失败", f"连接失败，请检查API配置和网络。\n错误信息: {e}") # 弹出错误对话框显示 API 连接失败信息
            self.chat_display.append(f"[Error] API 连接失败: {e}") # 在聊天显示区域显示 API 连接失败信息
            self.model_name_combo.clear() # 清空模型下拉框
            self.model_name_combo.addItem("API 连接失败") # 添加 "API 连接失败" 提示项
            self.model_name_combo.setEnabled(False) # 禁用模型下拉框
            self.send_button.setEnabled(False) # 禁用 "发送" 按钮
            self.stop_button.setEnabled(False) # 禁用 "停止" 按钮
            self.clear_button.setEnabled(False) # 禁用 "清除上下文" 按钮


    def get_model_list(self):
        """
        获取模型列表，并在模型下拉框中显示。
        """
        self.model_name_combo.clear() # 清空模型下拉框
        self.model_name_combo.addItem("正在获取模型列表...") # 添加 "正在获取模型列表..." 提示项
        self.model_name_combo.setEnabled(False) # 禁用模型下拉框

        self.model_list_thread = LLMModelListThread(self.llm_client) # 创建 LLMModelListThread 线程
        self.model_list_thread.models_fetched.connect(self.populate_model_dropdown) # 连接模型列表获取成功信号到 populate_model_dropdown 方法
        self.model_list_thread.error_fetching_models.connect(self.handle_model_list_error) # 连接模型列表获取失败信号到 handle_model_list_error 方法
        self.model_list_thread.start() # 启动模型列表获取线程

    def populate_model_dropdown(self, model_list):
        """
        填充模型下拉框，显示可用模型列表。

        Args:
            model_list (list): 模型名称列表。
        """
        self.model_name_combo.clear() # 清空模型下拉框
        self.model_name_combo.addItems(model_list) # 添加模型名称列表到下拉框
        if model_list:
            self.model_name_combo.setCurrentIndex(0) # 默认选择第一个模型
        else:
            self.model_name_combo.addItem("模型列表为空") # 如果模型列表为空，添加 "模型列表为空" 提示项
        self.model_name_combo.setEnabled(True) # 启用模型下拉框

    def handle_model_list_error(self, error_message):
        """
        处理获取模型列表错误，在模型下拉框中显示错误信息。

        Args:
            error_message (str): 错误信息。
        """
        self.model_name_combo.clear() # 清空模型下拉框
        self.model_name_combo.addItem(f"获取模型列表失败: {error_message}") # 添加错误提示信息到下拉框
        self.model_name_combo.setEnabled(False) # 禁用模型下拉框


    def send_message(self):
        """
        发送用户消息，创建 LLMChatThread 线程，处理 LLM 响应。
        """
        if not self.llm_client.client:
            QMessageBox.warning(self, "API 未连接", "请先点击 '连接' 按钮配置并连接 API。") # 弹出警告对话框提示 API 未连接
            return

        user_message = self.user_input.text().strip() # 获取用户输入的消息并去除首尾空格
        if not user_message:
            return # 如果用户输入为空，则直接返回

        self.chat_display.append(f"用户: {user_message}\n") # 将用户消息添加到聊天显示区域
        self.messages.append({"role": "user", "content": user_message}) # 将用户消息添加到对话消息列表中
        self.user_input.clear() # 清空用户输入框
        self.send_button.setEnabled(False) # 发送消息后禁用 "发送" 按钮，防止重复发送

        model_params_override = self.get_model_params_override() # 获取模型参数重载字典

        selected_model_name = self.model_name_combo.currentText() # 获取模型下拉框中选择的模型名称
        print(f"\n--- Debug - Selected Model Name from Dropdown: {selected_model_name} ---") # 调试输出选中的模型名称

        self.assistant_prefix_added = False #  !!!  每次发送用户消息前，重置 assistant_prefix_added 标记为 False  !!!

        # 创建 LLMChatThread 线程，并将 LLMClient 实例, 消息列表, 模型参数重载字典, 模型名称传递给线程
        self.llm_thread = LLMChatThread(self.llm_client, self.messages, model_params_override, selected_model_name)
        self.llm_thread.stream_output.connect(self.update_llm_output) # 连接流式输出信号到 update_llm_output 方法
        self.llm_thread.complete.connect(self.complete_output) # 连接完成信号到 complete_output 方法
        self.llm_thread.start() # 启动 LLM 聊天线程

    def get_model_params_override(self):
        """
        从 UI 界面获取用户设置的模型参数重载。

        Returns:
            dict: 模型参数重载字典，包含用户启用的模型参数和对应的值。
        """
        params = {} # 初始化参数字典
        if self.param_checkboxes['temperature'].isChecked(): # 如果 temperature 参数复选框被选中
            params['temperature'] = self.temp_spinbox.value() # 获取 temperature 参数值
        if self.param_checkboxes['top_p'].isChecked(): # 如果 top_p 参数复选框被选中
            params['top_p'] = self.top_p_spinbox.value() # 获取 top_p 参数值
        if self.param_checkboxes['max_tokens'].isChecked(): # 如果 max_tokens 参数复选框被选中
            params['max_tokens'] = int(self.max_tokens_spinbox.value()) # 获取 max_tokens 参数值，并转换为整数
        if self.param_checkboxes['frequency_penalty'].isChecked(): # 如果 frequency_penalty 参数复选框被选中
            params['frequency_penalty'] = self.frequency_penalty_spinbox.value() # 获取 frequency_penalty 参数值
        if self.param_checkboxes['presence_penalty'].isChecked(): # 如果 presence_penalty 参数复选框被选中
            params['presence_penalty'] = self.presence_penalty_spinbox.value() # 获取 presence_penalty 参数值
        return params # 返回参数字典


    def update_llm_output(self, chunk):
        """
        更新 LLM 输出，将 LLM 响应文本 chunk 添加到聊天显示区域，并添加 "助手: " 前缀 (仅在首次输出时添加)。

        Args:
            chunk (str): LLM 响应的文本 chunk。
        """
        prefix = "" # 初始化前缀为空字符串
        if not self.assistant_prefix_added: # 如果 assistant_prefix_added 标记为 False (表示尚未添加前缀)
            prefix = "助手: " # 设置前缀为 "助手: "
            self.assistant_prefix_added = True # 将 assistant_prefix_added 标记设置为 True，表示已添加前缀

        self.chat_display.moveCursor(self.chat_display.textCursor().End) # 移动光标到文本末尾，保证新内容显示在最下面
        self.chat_display.insertPlainText(f"{prefix}{chunk}") # 插入带有前缀 (或无前缀) 的 LLM 响应文本 chunk


    def complete_output(self):
        """
        LLM 输出完成后的处理，启用 "发送" 按钮。
        """
        self.chat_display.append("\n") # 添加换行符，分隔不同轮次的对话
        self.send_button.setEnabled(True) # 重新启用 "发送" 按钮

    def stop_llm(self):
        """
        停止 LLM 生成。 (目前尚未实现 LLM 停止生成的功能，这里只是一个空方法)
        """
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_thread.stop() # 尝试停止线程 (注意: 线程的 stop() 方法通常不安全，这里可能需要更完善的线程管理机制)
            self.chat_display.append("\n[LLM 输出已停止]\n") # 在聊天显示区域显示 "LLM 输出已停止" 消息
            self.send_button.setEnabled(True) # 停止后重新启用 "发送" 按钮


    def clear_context(self):
        """
        清除对话上下文，重置对话消息列表，清空聊天显示区域。
        """
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}] # 重置对话消息列表，只保留初始系统消息
        self.chat_display.clear() # 清空聊天显示区域
        self.chat_display.append("上下文已清除。\n") # 在聊天显示区域显示 "上下文已清除" 消息
        self.send_button.setEnabled(True) # 清除上下文后重新启用 "发送" 按钮


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow() # 创建 ChatWindow 实例
    window.resize(800, 700) # 设置窗口大小
    window.show() # 显示窗口
    sys.exit(app.exec_()) # 运行应用程序