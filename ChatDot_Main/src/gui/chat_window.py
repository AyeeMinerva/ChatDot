import os
os.environ['PYTHONIOENCODING'] = 'UTF-8'
import sys
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QTextEdit, QLineEdit, QWidget, QPushButton, QHBoxLayout, QMessageBox, QSizePolicy, QScrollArea
from PyQt5.QtCore import Qt
from client.llm_client import LLMClient
from client.llm_interaction import LLMChatThread
from gui.components.message_bubble import MessageBubble
from persistence.settings_persistence import load_settings  # 添加导入

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简洁 LLM 聊天窗口 (重构版)")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.llm_client = LLMClient()
        self.llm_thread = None
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.assistant_prefix_added = False
        self.init_ui()
        self.enable_send_buttons()  # 初始化后立即启用按钮
        self.load_saved_settings()  # 加载保存的设置

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 创建消息滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_content = QWidget(self.scroll_area)
        self.messages_layout = QVBoxLayout(self.scroll_content)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        self.user_input_layout = QHBoxLayout()
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("请输入消息...")
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.user_input.returnPressed.connect(self.send_message)
        self.user_input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("发送", self)
        self.send_button.clicked.connect(self.send_message)
        self.user_input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.user_input_layout)

        self.operation_layout = QHBoxLayout()
        self.stop_button = QPushButton("停止", self)
        self.stop_button.clicked.connect(self.stop_llm)
        self.operation_layout.addWidget(self.stop_button)

        self.clear_button = QPushButton("清除上下文", self)
        self.clear_button.clicked.connect(self.clear_context)
        self.operation_layout.addWidget(self.clear_button)
        self.layout.addLayout(self.operation_layout)

    def enable_send_buttons(self):
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def send_message(self, retry=False):
        if not retry:
            user_message = self.user_input.text().strip()
            if not user_message:
                return
            self.add_message_bubble(user_message, "user")
            self.messages.append({"role": "user", "content": user_message})
            self.user_input.clear()

        # 改为无提示直接返回
        if not self.llm_client.client:
            return

        # 发送时禁用发送按钮，但启用停止按钮
        self.send_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        model_params_override = {}
        selected_model_name = self.llm_client.get_model_name()
        if not selected_model_name:
            selected_model_name = "gpt-3.5-turbo"
            QMessageBox.warning(self, "模型未选择", "请在设置中选择 LLM 模型，当前使用默认模型 gpt-3.5-turbo。")
        
        print(f"\n--- Debug - Selected Model Name from llm_client: {selected_model_name} ---")
        self.assistant_prefix_added = False
        self.llm_thread = LLMChatThread(self.llm_client, self.messages, model_params_override, selected_model_name)
        self.llm_thread.stream_output.connect(self.update_llm_output)
        self.llm_thread.complete.connect(self.complete_output)
        self.llm_thread.start()

    def update_llm_output(self, chunk):
        if not self.assistant_prefix_added:
            # 添加新的回复消息到历史记录
            self.messages.append({"role": "assistant", "content": chunk})
            self.add_message_bubble(chunk, "assistant")
            self.assistant_prefix_added = True
        else:
            # 更新最后一个气泡的内容和历史记录
            last_item = self.messages_layout.itemAt(self.messages_layout.count() - 2)
            if last_item and isinstance(last_item.widget(), MessageBubble):
                bubble = last_item.widget()
                current_text = bubble.content_edit.toPlainText()
                new_text = current_text + chunk
                bubble.content_edit.setText(new_text)
                self.messages[-1]["content"] = new_text

    def complete_output(self):
        # 不再使用 chat_display
        self.enable_send_buttons()

    def stop_llm(self):
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_thread.stop()
            self.llm_thread.wait()
            self.chat_display.append("\n[LLM 输出已停止]\n")
            self.enable_send_buttons()  # 停止后启用所有按钮

    def clear_context(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        # 清除所有消息气泡
        while self.messages_layout.count() > 1:  # 保留最后的 stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.enable_send_buttons()

    def add_message_bubble(self, message, role):
        # 索引应该就是消息在 messages 列表中的实际位置
        index = len(self.messages) - 1
        bubble = MessageBubble(message, index, role)
        bubble.delete_requested.connect(self.delete_message)
        bubble.edit_completed.connect(self.edit_message)
        bubble.retry_requested.connect(self.retry_message)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        # 滚动到底部
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def delete_message(self, index):
        if 0 <= index < len(self.messages):
            # 从消息列表中删除
            self.messages.pop(index)
            
            # 从布局中找到对应索引的组件并删除
            for i in range(self.messages_layout.count() - 1):  # -1 排除最后的 stretch
                item = self.messages_layout.itemAt(i)
                if item and isinstance(item.widget(), MessageBubble):
                    bubble = item.widget()
                    if bubble.index == index:
                        self.messages_layout.removeItem(item)
                        bubble.deleteLater()
                        break
            
            # 更新剩余消息气泡的索引
            for i in range(self.messages_layout.count() - 1):
                item = self.messages_layout.itemAt(i)
                if item and isinstance(item.widget(), MessageBubble):
                    bubble = item.widget()
                    if bubble.index > index:
                        bubble.index -= 1

    def edit_message(self, index, new_text):
        if 0 <= index < len(self.messages):
            self.messages[index]["content"] = new_text

    def retry_message(self, index):
        if index == len(self.messages) - 1:  # 只允许重试最后一条消息
            # 保存当前回复作为候选
            current_response = self.messages[index]["content"]
            last_bubble = self.messages_layout.itemAt(index).widget()
            if last_bubble:
                last_bubble.add_alternative(current_response)
            
            # 获取到该条消息为止的所有历史记录
            retry_messages = self.messages[:index]
            self.messages = retry_messages
            # 发起新的请求
            self.send_message(retry=True)
        else:
            print("只能重试最后一条消息")

    def handle_error_response(self, error_message):
        # 将错误消息添加到消息列表，确保索引正确
        self.messages.append({"role": "error", "content": f"[系统错误]: {error_message}"})
        # 添加错误消息气泡，传入正确的索引
        self.add_message_bubble(f"[系统错误]: {error_message}", "error")

    def load_saved_settings(self):
        settings = load_settings()
        api_key = settings.get('api_key', '')
        api_base = settings.get('api_base', '')
        model_name = settings.get('model_name', '')
        
        if api_key and api_base:
            try:
                self.llm_client.set_api_config(api_key=api_key, api_base=api_base)
                if model_name:
                    self.llm_client.set_model_name(model_name)
            except Exception as e:
                print(f"加载API配置失败: {e}")
