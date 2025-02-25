import os
os.environ['PYTHONIOENCODING'] = 'UTF-8'
import sys
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QSizePolicy, QScrollArea, QDesktopWidget, QApplication, QApplication
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer
from client.llm_client import LLMClient
from client.llm_interaction import LLMChatThread
from gui.components.message_bubble import MessageBubble
from persistence.settings_persistence import load_settings
from PyQt5.QtGui import QCursor

class ChatWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Chat Window")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.llm_client = LLMClient()
        self.llm_thread = None
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.assistant_prefix_added = False
        self.init_ui()
        self.enable_send_buttons()
        self.load_saved_settings()

    def init_ui(self):
        # 窗口基础设置
        self.screen = QDesktopWidget().availableGeometry()
        #最小宽度和高度
        # self.setMinimumWidth(400)
        # self.setMinimumHeight(300)
        self.resize(500, 400)
        #self.max_auto_height = int(self.screen.height() * 0.8)

        # 主体布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # 消息显示区域（滚动）
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 自动显示滚动条

        self.scroll_content = QWidget(self.scroll_area)
        self.messages_layout = QVBoxLayout(self.scroll_content)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()  # 消息置底的关键
        self.scroll_content.setLayout(self.messages_layout)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # 用户输入区域
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

        # 操作按钮区域
        self.operation_layout = QHBoxLayout()
        self.stop_button = QPushButton("停止", self)
        self.stop_button.clicked.connect(self.stop_llm)
        self.operation_layout.addWidget(self.stop_button)

        self.clear_button = QPushButton("清除上下文", self)
        self.clear_button.clicked.connect(self.clear_context)
        self.operation_layout.addWidget(self.clear_button)
        self.layout.addLayout(self.operation_layout)

        # 初始滚动到底部
        QTimer.singleShot(0, self.scroll_to_bottom)

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

        if not self.llm_client.client:
            QMessageBox.warning(self, "API 未配置", "请先在设置中配置 API 连接。")
            return

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
        # 始终滚动到底部
        self.scroll_to_bottom()

    def complete_output(self):
        self.enable_send_buttons()
        # 输出完成后再次调整窗口大小
        #self.adjustWindowSize()

    def stop_llm(self):
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_thread.stop()
            self.llm_thread.wait()
            self.enable_send_buttons()

    def clear_context(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        # 清除所有消息气泡
        while self.messages_layout.count() > 1:  # 保留最后的 stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.enable_send_buttons()
        # 清除后调整窗口大小
        #self.adjustWindowSize()

    def add_message_bubble(self, message, role):
        index = len(self.messages) - 1
        bubble = MessageBubble(message, index, role)
        bubble.delete_requested.connect(self.delete_message)
        bubble.edit_completed.connect(self.edit_message)
        bubble.retry_requested.connect(self.retry_message)
        # 在 stretch 前插入消息气泡
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        # 消息气泡添加后调整窗口大小
        #self.adjustWindowSize()
        # 滚动到底部
        self.scroll_to_bottom()

    def delete_message(self, index):
        if 0 <= index < len(self.messages):
            self.messages.pop(index)
            # 移除布局中的组件
            for i in range(self.messages_layout.count()):
                item = self.messages_layout.itemAt(i)
                if item and isinstance(item.widget(), MessageBubble):
                    bubble = item.widget()
                    if bubble.index == index:
                        self.messages_layout.removeItem(item)
                        bubble.deleteLater()
                        break
            # 更新剩余消息气泡的索引
            for i in range(self.messages_layout.count()):
                item = self.messages_layout.itemAt(i)
                if item and isinstance(item.widget(), MessageBubble):
                    bubble = item.widget()
                    if bubble.index > index:
                        bubble.index -= 1
            # 删除消息后调整窗口大小
            #self.adjustWindowSize()

    def edit_message(self, index, new_text):
        if 0 <= index < len(self.messages):
            self.messages[index]["content"] = new_text
        # 编辑消息后调整窗口大小
        #self.adjustWindowSize()

    def retry_message(self, index):
        if index == len(self.messages) - 1:
            current_response = self.messages[index]["content"]
            last_bubble = self.messages_layout.itemAt(index).widget()
            if last_bubble:
                last_bubble.add_alternative(current_response)

            retry_messages = self.messages[:index]
            self.messages = retry_messages
            self.send_message(retry=True)
        else:
            print("只能重试最后一条消息")

    def handle_error_response(self, error_message):
        self.messages.append({"role": "error", "content": f"[系统错误]: {error_message}"})
        self.add_message_bubble(f"[系统错误]: {error_message}", "error")

    def load_saved_settings(self):
        settings = load_settings()
        api_keys = settings.get('api_keys', [])
        api_base = settings.get('api_base', '')
        model_name = settings.get('model_name', '')

        if api_keys and api_base:
            try:
                self.llm_client.set_api_config(api_keys=api_keys, api_base=api_base)
                if model_name:
                    self.llm_client.set_model_name(model_name)
            except Exception as e:
                print(f"加载API配置失败: {e}")

    def scroll_to_bottom(self):
        """滚动到底部"""
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    #此函数已被移除,因为性能过差且不是必要的
    # def adjustWindowSize(self):
    #     """调整窗口大小，确保内容完整显示且不超出屏幕"""
    #     #print("正在调整窗口大小")
    #     content_height = 0
    #     for i in range(self.messages_layout.count()):
    #         item = self.messages_layout.itemAt(i)
    #         if item and item.widget():
    #             content_height += item.widget().height() + self.messages_layout.spacing()

    #     total_height = (content_height +
    #                     self.user_input.height() +
    #                     self.stop_button.height() +
    #                     self.layout.spacing() * 3 +
    #                     self.layout.contentsMargins().top() +
    #                     self.layout.contentsMargins().bottom() +
    #                     50)  # 额外空间

    #     total_height = min(total_height, self.max_auto_height)

    #     # 获取当前窗口位置和大小
    #     current_pos = self.pos()
    #     current_height = self.height()

    #     # 计算新的窗口位置
    #     new_y = current_pos.y() - (total_height - current_height)
    #     if new_y < self.screen.top():
    #         new_y = self.screen.top()

    #    self.setGeometry(QRect(current_pos.x(), new_y, self.width(), total_height))

    def toggleChatWindow(self):
        """显示/隐藏聊天窗口"""
        if self.isVisible():
            self.hide()
        else:
            # 获取悬浮球位置
            ball_pos = self.parent().mapToGlobal(QPoint(0, 0))

            #获取屏幕
            desktop = QApplication.desktop()
            screen_number = desktop.screenNumber(ball_pos)
            screen = desktop.screenGeometry(screen_number)
            
            # 计算初始位置（在悬浮球右下方）
            chat_window_x = ball_pos.x() + self.parent().width() + 10
            chat_window_y = ball_pos.y() + self.parent().height()

            #窗口超出屏幕边界时，调整位置到屏幕边缘
            if chat_window_x + self.width() > screen.right() and chat_window_y + self.height() > screen.bottom():
                chat_window_x = self.parent().x() - self.parent().width() - self.width()
                chat_window_y = screen.bottom() - self.height()

            if chat_window_x < screen.left():
                chat_window_x = screen.left()
            elif chat_window_x + self.width() > screen.right():
                chat_window_x = screen.right() - self.width()
            
            if chat_window_y < screen.top():
                chat_window_y = screen.top()

            elif chat_window_y + self.height() > screen.bottom():
                chat_window_y = screen.bottom() - self.height()


            # 确保窗口不会超出屏幕边界
            # chat_window_x = max(chat_window_x, self.screen.left())
            # chat_window_x = min(chat_window_x, self.screen.right() - self.width())
            # chat_window_y = max(chat_window_y, self.screen.top())
            # chat_window_y = min(chat_window_y, self.screen.bottom() - self.height())

            self.move(chat_window_x, chat_window_y)
            self.show()
            self.activateWindow()

    def showEvent(self, event):
        """窗口显示时滚动到底部"""
        super().showEvent(event)
        QTimer.singleShot(0, self.scroll_to_bottom)
