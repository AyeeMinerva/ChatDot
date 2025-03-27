from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from core.global_managers.service_manager import ServiceManager

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.service_manager = ServiceManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chat Interface")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("输入消息...")
        layout.addWidget(self.user_input)

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_message(self):
        user_message = self.user_input.text().strip()
        if not user_message:
            QMessageBox.warning(self, "警告", "消息不能为空！")
            return

        self.chat_display.append(f"用户: {user_message}")
        self.user_input.clear()

        chat_service = self.service_manager.get_service("chat_service")
        try:
            response = chat_service.send_message(user_message)
            self.chat_display.append(f"助手: {response}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送消息时出错: {str(e)}")