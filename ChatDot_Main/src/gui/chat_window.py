from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLineEdit,
                           QPushButton, QHBoxLayout, QMessageBox, QSizePolicy,
                           QScrollArea, QDesktopWidget, QApplication)
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QCursor, QColor

from core.bootstrap import Bootstrap
from core.global_managers.service_manager import ServiceManager
from gui.components.message_bubble import MessageBubble

class ChatThread(QThread):
    """处理LLM响应的线程"""
    chunk_received = pyqtSignal(str)
    completed = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, chat_service, user_message):
        super().__init__()
        self.chat_service = chat_service
        self.user_message = user_message
        self.is_running = True

    def run(self):
        try:
            response_iterator = self.chat_service.send_message(self.user_message, is_stream=True)
            for chunk in response_iterator:
                if not self.is_running:
                    break
                self.chunk_received.emit(chunk)
            if self.is_running:
                self.completed.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

# 添加STT处理线程
class STTThread(QThread):
    """语音识别线程"""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, stt_service):
        super().__init__()
        self.stt_service = stt_service
        self.is_running = True
    
    def run(self):
        import asyncio
        
        # 识别结果回调
        def on_segment_recognized(text):
            if self.is_running:
                self.text_recognized.emit(text)
        
        async def run_recognition():
            try:
                # 初始化STT服务
                if not await self.stt_service.initialize_async():
                    self.error_occurred.emit("无法初始化语音识别服务")
                    return
                
                # 设置回调
                self.stt_service.segment_callbacks = []
                self.stt_service.add_segment_callback(on_segment_recognized)
                
                # 开始识别
                if not await self.stt_service.start_recognition_async():
                    self.error_occurred.emit("启动语音识别失败")
                    return
                
                # 等待停止信号
                while self.is_running:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                self.error_occurred.emit(f"语音识别过程中出错: {str(e)}")
            finally:
                # 确保服务正确关闭
                try:
                    await self.stt_service.stop_recognition_async()
                    await self.stt_service.shutdown_async()
                except Exception as e:
                    self.error_occurred.emit(f"关闭语音识别服务时出错: {str(e)}")
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_recognition())
        finally:
            loop.close()
    
    def stop(self):
        """停止语音识别线程"""
        self.is_running = False
        self.wait()  # 等待线程结束

class ChatWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_window()
        self._init_services()
        self.init_ui()
        self.llm_thread = None  # 初始化llm_thread

    def _init_window(self):
        """初始化窗口基础属性"""
        # 窗口基础设置
        self.setWindowTitle("ChatDot")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # 透明度设置
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("QMainWindow {background: transparent;}")

        # 拖放功能
        self.setAcceptDrops(True)

        # 获取屏幕信息用于布局
        self.screen = QDesktopWidget().availableGeometry()
        self.resize(500, 400)

    def _init_services(self):
        """初始化核心服务"""
        # 初始化 Bootstrap
        self.bootstrap = Bootstrap()
        self.bootstrap.initialize()

        # 使用 Bootstrap 中已有的 ServiceManager，而不是创建新实例
        self.service_manager = self.bootstrap.service_manager

        # 获取核心服务
        self.chat_service = self.service_manager.get_service("chat_service")
        self.context_handle_service = self.service_manager.get_service("context_handle_service")
        self.llm_service = self.service_manager.get_service("llm_service")

        # 初始化消息列表
        self.messages = []
        self.assistant_prefix_added = False

    def init_ui(self):
        """初始化UI布局"""
        # 主体布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # 设置背景透明
        self.central_widget.setStyleSheet("QWidget { background: transparent; }")
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 添加消息区域
        self._init_message_area()

        # 添加输入区域
        self._init_input_area()

        # 初始滚动到底部
        QTimer.singleShot(0, self.scroll_to_bottom)

    def _init_message_area(self):
        """初始化消息显示区域"""
        # 滚动区域设置
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 滚动区域样式
        self.scroll_area.setStyleSheet(
            "QScrollArea { background: transparent; border: 0px; }"
        )
        self.scroll_area.viewport().setStyleSheet(
            "QWidget{background: transparent;}"
        )

        # 消息内容区域
        self.scroll_content = QWidget(self.scroll_area)
        self.messages_layout = QVBoxLayout(self.scroll_content)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()

        # 设置内容区域样式
        self.scroll_content.setStyleSheet("QWidget { background: transparent; }")

        # 组装滚动区域
        self.scroll_content.setLayout(self.messages_layout)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

    def _init_input_area(self):
        """初始化输入区域"""
        # 输入区域布局
        self.user_input_layout = QHBoxLayout()

        # 输入框
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("请输入消息...")
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.user_input.returnPressed.connect(self.send_message)
        self.user_input.setStyleSheet(
            "QLineEdit { background: rgba(255, 255, 255, 150); "
            "border: 1px solid rgba(200, 200, 200, 150); }"
        )

        # 语音输入按钮
        self.voice_button = QPushButton("🎤", self)
        self.voice_button.setToolTip("语音输入")
        self.voice_button.setFixedSize(30, 30)
        self.voice_button.clicked.connect(self.toggle_voice_input)
        self.voice_button.setStyleSheet(
            "QPushButton { background: rgba(220, 220, 220, 150); border-radius: 15px; }"
            "QPushButton:hover { background: rgba(200, 200, 200, 200); }"
            "QPushButton:pressed { background: rgba(180, 180, 180, 200); }"
        )

        # 发送按钮
        self.send_button = QPushButton("发送", self)
        self.send_button.clicked.connect(self.send_message)
        
        # 添加到布局
        self.user_input_layout.addWidget(self.user_input)
        self.user_input_layout.addWidget(self.voice_button)
        self.user_input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.user_input_layout)

        # 初始化语音输入状态
        self.is_voice_active = False
        self.speech_thread = None

    def toggle_voice_input(self):
        """切换语音输入模式"""
        stt_service = self.service_manager.get_service("stt_service")
        
        # 检查STT是否启用
        if not stt_service.settings.get_setting("enabled"):
            QMessageBox.warning(self, "STT未启用", "请在设置中启用语音识别功能")
            return
        
        if self.is_voice_active:
            # 停止语音输入
            self.stop_voice_input()
        else:
            # 开始语音输入
            self.start_voice_input()

    def start_voice_input(self):
        """开始语音输入"""
        stt_service = self.service_manager.get_service("stt_service")
        
        # 设置按钮为激活状态
        self.voice_button.setStyleSheet(
            "QPushButton { background: rgba(255, 100, 100, 200); border-radius: 15px; }"
            "QPushButton:hover { background: rgba(255, 80, 80, 220); }"
        )
        self.voice_button.setText("■")
        self.voice_button.setToolTip("停止语音输入")
        self.user_input.setPlaceholderText("正在听取语音...")
        self.is_voice_active = True
        
        # 创建并启动语音识别线程
        self.speech_thread = STTThread(stt_service)
        self.speech_thread.text_recognized.connect(self.on_speech_recognized)
        self.speech_thread.error_occurred.connect(self.on_speech_error)
        self.speech_thread.start()

    def stop_voice_input(self):
        """停止语音输入"""
        # 还原按钮状态
        self.voice_button.setStyleSheet(
            "QPushButton { background: rgba(220, 220, 220, 150); border-radius: 15px; }"
            "QPushButton:hover { background: rgba(200, 200, 200, 200); }"
            "QPushButton:pressed { background: rgba(180, 180, 180, 200); }"
        )
        self.voice_button.setText("🎤")
        self.voice_button.setToolTip("语音输入")
        self.user_input.setPlaceholderText("请输入消息...")
        self.is_voice_active = False
        
        # 停止语音识别线程
        if self.speech_thread and self.speech_thread.isRunning():
            self.speech_thread.stop()

    def on_speech_recognized(self, text):
        """当识别到语音时的回调"""
        if text:
            self.user_input.setText(text)
            # 如果识别结果有意义，自动发送
            if len(text) > 3:  # 简单过滤太短的结果
                self.send_message()
            else:
                # 短结果可能是错误识别，显示但不自动发送
                self.stop_voice_input()

    def on_speech_error(self, error_message):
        """语音识别错误的回调"""
        QMessageBox.warning(self, "语音识别错误", error_message)
        self.stop_voice_input()

    def send_message(self, retry=False):
        if not retry:
            user_message = self.user_input.text().strip()
            if not user_message:
                return

            self.add_message_bubble(user_message, "user")
            self.user_input.clear()

        # 停止之前的线程
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_thread.stop()
            self.llm_thread.wait()

        # 创建新的线程
        self.llm_thread = ChatThread(self.chat_service, user_message)
        self.llm_thread.chunk_received.connect(self.update_llm_output)
        self.llm_thread.completed.connect(self.complete_output)
        self.llm_thread.error.connect(self.handle_error_response)
        self.llm_thread.start()

    def update_llm_output(self, chunk):
        if not self.assistant_prefix_added:
            self.add_message_bubble(chunk, "assistant")
            self.assistant_prefix_added = True
        else:
            # 更新最后一个气泡的内容
            last_item = self.messages_layout.itemAt(self.messages_layout.count() - 2)
            if last_item and isinstance(last_item.widget(), MessageBubble):
                bubble = last_item.widget()
                current_text = bubble.content_edit.toPlainText()
                new_text = current_text + chunk
                bubble.content_edit.setText(new_text)

        self.scroll_to_bottom()

    def complete_output(self):
        self.enable_send_buttons()
        self.assistant_prefix_added = False

    def handle_error_response(self, error_message):
        QMessageBox.critical(self, "错误", f"发生错误: {error_message}")
        self.enable_send_buttons()
        self.assistant_prefix_added = False

    def clear_context(self):
        self.chat_service.clear_context()

        # 清除UI中的消息气泡
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.enable_send_buttons()

    def get_available_handlers(self):
        """获取可用的上下文处理器列表"""
        return self.context_handle_service.get_available_handlers()

    def switch_handler(self, handler_name: str):
        """切换上下文处理器"""
        success = self.context_handle_service.set_current_handler(handler_name)
        if success:
            QMessageBox.information(self, "成功", f"已切换到处理器: {handler_name}")
        else:
            QMessageBox.warning(self, "错误", "切换处理器失败")


    def add_message_bubble(self, message, role):
        index = len(self.messages) - 1
        bubble = MessageBubble(message, index, role)
        bubble.delete_requested.connect(self.delete_message)
        bubble.edit_completed.connect(self.edit_message)
        bubble.retry_requested.connect(self.retry_message)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.scroll_to_bottom()

    def delete_message(self, index):
        if 0 <= index < len(self.messages):
            # 使用chat_service删除消息
            messages = self.chat_service.get_messages()
            messages.pop(index)
            self.chat_service.set_messages(messages)

            # 更新UI
            for i in range(self.messages_layout.count()):
                item = self.messages_layout.itemAt(i)
                if item and isinstance(item.widget(), MessageBubble):
                    item.widget().deleteLater()
            self.messages_layout.removeItem(item)

    def edit_message(self, index, new_text):
        # 使用chat_service编辑消息
        messages = self.chat_service.get_messages()
        if 0 <= index < len(messages):
            messages[index]["content"] = new_text
            self.chat_service.set_messages(messages)

    def retry_message(self, index):
        messages = self.chat_service.get_messages()
        if index == len(messages) - 1:
            current_response = messages[index]["content"]
            last_bubble = self.messages_layout.itemAt(index).widget()
            if last_bubble:
                last_bubble.add_alternative(current_response)

            retry_messages = messages[:index]
            self.chat_service.set_messages(retry_messages)
            self.send_message(retry=True)

    def toggleChatWindow(self):
        """显示/隐藏聊天窗口"""
        if self.isVisible():
            self.hide()
        else:
            ball_pos = self.parent().mapToGlobal(QPoint(0, 0))
            desktop = QApplication.desktop()
            screen_number = desktop.screenNumber(ball_pos)
            screen = desktop.screenGeometry(screen_number)

            # 计算窗口位置
            chat_window_x = ball_pos.x() + self.parent().width() + 10
            chat_window_y = ball_pos.y() + self.parent().height()

            # 确保窗口在屏幕内
            if chat_window_x + self.width() > screen.right():
                chat_window_x = screen.right() - self.width()
            if chat_window_y + self.height() > screen.bottom():
                chat_window_y = screen.bottom() - self.height()

            self.move(chat_window_x, chat_window_y)
            self.show()
            self.activateWindow()

    def showEvent(self, event):
        """窗口显示时滚动到底部"""
        super().showEvent(event)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """滚动到底部"""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith('.json'):
                try:
                    # 使用chat_service导入历史记录
                    self.chat_service.import_history(file_path)
                    self.load_chat_history(self.chat_service.get_messages())
                except Exception as e:
                    QMessageBox.warning(self, "导入失败", f"导入历史记录失败: {str(e)}")
            else:
                QMessageBox.warning(self, "格式错误", "只支持导入.json格式的历史记录文件")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def load_chat_history(self, messages):
        """直接加载消息列表"""
        try:
            # 清空显示
            self.clear_chat_display()
            
            # 添加消息
            for msg in messages:
                if msg["role"] not in ["system"]:
                    self.add_message_bubble(msg["content"], msg["role"])
                    
            # 滚动到底部
            self.scroll_to_bottom()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载聊天历史失败：{str(e)}")


    def enable_send_buttons(self):
        """启用所有按钮"""
        self.send_button.setEnabled(True)

    def stop_llm(self):
        """停止 LLM 线程"""
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_thread.stop()
            # self.llm_thread.wait()
            self.llm_thread = None  # 重置 llm_thread
        self.enable_send_buttons()
        self.assistant_prefix_added = False

    def update_chat_display(self, file_path):
        """更新聊天显示"""
        try:
            # 先导入历史记录
            self.chat_service.import_history(file_path)
            
            # 清空当前显示
            self.clear_chat_display()
            
            # 加载历史消息
            messages = self.chat_service.get_messages()
            for message in messages:
                if message["role"] not in ["system"]:
                    self.add_message_bubble(message["content"], message["role"])
                    
            # 滚动到底部
            self.scroll_to_bottom()
            
            # 显示成功消息
            QMessageBox.information(self, "成功", "历史记录已加载")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"更新聊天显示失败：{str(e)}")

    def clear_chat_display(self):
        """清空聊天显示区域"""
        # 使用正确的布局变量名
        while self.messages_layout.count() > 1:  # 保留最后的 stretch
            item = self.messages_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def connect_history_settings(self, history_settings):
        """连接历史设置页面的信号"""
        self.history_settings = history_settings
        self.history_settings.load_history_requested.connect(self.update_chat_display)