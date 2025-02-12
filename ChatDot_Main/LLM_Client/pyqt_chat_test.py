import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTextEdit, QLineEdit, QWidget, QPushButton
)
from PyQt5.QtCore import QThread, pyqtSignal
from llm_client import LLMClient  # 引用封装类


# 与 LLM 通信的线程
class LLMChatThread(QThread):
    stream_output = pyqtSignal(str, bool)  # 信号传递流式输出内容和是否为新消息
    complete = pyqtSignal()  # 信号传递流式结束标志

    def __init__(self, llm_client, messages):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.running = True
        self.should_stop = False  # 标志位，用于停止线程

    def run(self):
        # 更新 LLMClient 的上下文
        self.llm_client.clear_context()
        for message in self.messages:
            self.llm_client.add_message(message["role"], message["content"])

        try:
            # 流式通信
            for chunk in self.llm_client.communicate(stream=True):
                if not self.running or self.should_stop:
                    break
                self.stream_output.emit(chunk, False)  # 发出流式内容
        except RuntimeError as e:
            self.stream_output.emit(f"\n[Error]: {e}", False)
        finally:
            self.complete.emit()

    def stop(self):
        self.running = False
        self.should_stop = True
        self.quit()


# PyQt 主窗口
class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.llm_client = LLMClient()  # 初始化 LLM 客户端
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chat with LLM")

        # 设置布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 显示聊天记录的文本框
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        # 用户输入框
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText(">> 等待用户输入...")
        self.user_input.returnPressed.connect(self.send_message)
        self.layout.addWidget(self.user_input)

        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_llm)
        self.layout.addWidget(self.stop_button)

        # 清除上下文按钮
        self.clear_button = QPushButton("清除上下文")
        self.clear_button.clicked.connect(self.clear_context)
        self.layout.addWidget(self.clear_button)

    def send_message(self):
        user_text = self.user_input.text().strip()
        if not user_text:
            return

        # 添加用户消息到聊天记录
        self.chat_display.append(f"用户：{user_text}")
        self.messages.append({"role": "user", "content": user_text})
        self.user_input.clear()

        # 停止正在运行的线程
        if hasattr(self, 'llm_thread') and self.llm_thread.isRunning():
            self.llm_thread.stop()
            self.llm_thread.wait()

        # 创建新的线程处理 LLM 输出
        self.llm_thread = LLMChatThread(self.llm_client, self.messages)
        self.llm_thread.stream_output.connect(self.update_llm_output)
        self.llm_thread.complete.connect(self.complete_output)
        self.llm_thread.start()

    def update_llm_output(self, content, is_new_message):
        if is_new_message:
            self.chat_display.append(f"LLM: {content}")
            self.messages.append({"role": "assistant", "content": content})
        else:
            self.chat_display.insertPlainText(content)
            if self.messages[-1]["role"] == "assistant":
                self.messages[-1]["content"] += content
        self.chat_display.moveCursor(self.chat_display.textCursor().End)

    def complete_output(self):
        self.chat_display.append("")  # 换行以表示完成
        if hasattr(self, 'llm_thread'):
            self.llm_thread.stop()

    def stop_llm(self):
        if hasattr(self, 'llm_thread') and self.llm_thread.isRunning():
            self.llm_thread.stop()
            self.chat_display.append("LLM: 输出已停止。")

    def clear_context(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.chat_display.append("上下文已清除。")

    def closeEvent(self, event):
        if hasattr(self, 'llm_thread') and self.llm_thread.isRunning():
            self.llm_thread.stop()
        event.accept()


# 启动程序
if __name__ == "__main__":
    app = QApplication(sys.argv)
    chat_window = ChatWindow()
    chat_window.resize(600, 400)
    chat_window.show()
    sys.exit(app.exec_())
