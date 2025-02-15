import os
os.environ['PYTHONIOENCODING'] = 'UTF-8'

import sys
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QTextEdit, QLineEdit, \
    QWidget, QPushButton, QHBoxLayout, QMessageBox, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt
from llm_client import LLMClient  # 确保使用相对路径导入
from llm_interaction import LLMChatThread  # 确保使用相对路径导入


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简洁 LLM 聊天窗口 (重写版)")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.llm_client = LLMClient()  #  !!!  保留 llm_client 实例，但不在此处进行 API 配置 !!!
        self.llm_thread = None

        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.assistant_prefix_added = False

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 1. 聊天显示区域 (保持不变)
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.chat_display)

        # 2. 用户输入区域 (保持不变)
        self.user_input_layout = QHBoxLayout()
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("请输入消息...")
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.user_input.returnPressed.connect(self.send_message)
        self.user_input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("发送", self)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)  #  !!!  初始禁用发送按钮，API 连接成功后启用 !!!
        self.user_input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.user_input_layout)


        # 3. 操作按钮区域 (保留停止和清除上下文按钮，移除参数配置区域)
        self.operation_layout = QHBoxLayout()
        self.stop_button = QPushButton("停止", self)
        self.stop_button.clicked.connect(self.stop_llm)
        self.stop_button.setEnabled(False)
        self.operation_layout.addWidget(self.stop_button)

        self.clear_button = QPushButton("清除上下文", self)
        self.clear_button.clicked.connect(self.clear_context)
        self.clear_button.setEnabled(False)
        self.operation_layout.addWidget(self.clear_button)
        self.layout.addLayout(self.operation_layout) #  !!!  操作按钮区域添加到主布局 !!!


        self.setLayout(self.layout)


    def enable_send_buttons(self): #  !!!  新增方法：启用发送和操作按钮  !!!
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(True)


    def send_message(self):
        if not self.llm_client.client: #  !!!  仍然需要检查 llm_client.client 是否已配置 !!!
            QMessageBox.warning(self, "API 未连接", "请先在设置中配置并连接 API。") #  !!!  修改提示信息 !!!
            return

        user_message = self.user_input.text().strip()
        if not user_message:
            return

        self.chat_display.append(f"用户: {user_message}\n")
        self.messages.append({"role": "user", "content": user_message})
        self.user_input.clear()
        self.send_button.setEnabled(False)

        #  !!!  模型参数应该从 llm_client 中获取，而不是从 ChatWindow 内部 !!!
        #  !!!  ChatWindow 不再管理模型参数，参数管理全部交给 SettingWindow 和 llm_client !!!
        model_params_override = {} #  !!!  不再从 UI 获取参数，直接传递空字典或从 llm_client 获取默认参数 !!!


        selected_model_name = self.llm_client.get_model_name() #  !!!  从 llm_client 获取当前模型名称 !!!
        if not selected_model_name:
            selected_model_name = "gpt-3.5-turbo" #  !!!  如果 llm_client 中没有设置模型，使用默认模型 !!!
            QMessageBox.warning(self, "模型未选择", "请在设置中选择 LLM 模型，当前使用默认模型 gpt-3.5-turbo。")


        print(f"\n--- Debug - Selected Model Name from llm_client: {selected_model_name} ---")

        self.assistant_prefix_added = False

        self.llm_thread = LLMChatThread(self.llm_client, self.messages, model_params_override, selected_model_name) #  !!!  使用 llm_interaction.LLMChatThread !!!
        self.llm_thread.stream_output.connect(self.update_llm_output)
        self.llm_thread.complete.connect(self.complete_output)
        self.llm_thread.start()



    def update_llm_output(self, chunk):
        prefix = ""
        if not self.assistant_prefix_added:
            prefix = "助手: "
            self.assistant_prefix_added = True

        self.chat_display.moveCursor(self.chat_display.textCursor().End)
        self.chat_display.insertPlainText(f"{prefix}{chunk}")


    def complete_output(self):
        self.chat_display.append("\n")
        self.send_button.setEnabled(True)

    def stop_llm(self):
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_thread.stop()
            self.chat_display.append("\n[LLM 输出已停止]\n")
            self.send_button.setEnabled(True)


    def clear_context(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.chat_display.clear()
        self.chat_display.append("上下文已清除。\n")
        self.send_button.setEnabled(True)