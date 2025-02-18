from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMenu, QAction, QTextEdit, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QTextCursor

class MessageBubble(QWidget):
    delete_requested = pyqtSignal(int)  # 删除信号
    edit_completed = pyqtSignal(int, str)  # 编辑完成信号
    retry_requested = pyqtSignal(int)  # 重试信号
    
    def __init__(self, message, index, role="user", parent=None):
        super().__init__(parent)
        self.message = message
        self.index = index
        self.role = role
        self.editing = False
        self.alternatives = []  # 存储平行候选回复
        self.current_alt_index = 0  # 当前显示的候选回复索引
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建顶部按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)

        if self.role == "assistant":
            retry_button = QPushButton("🔄", self)
            retry_button.setFixedSize(25, 25)
            retry_button.clicked.connect(lambda: self.retry_requested.emit(self.index))
            button_layout.addWidget(retry_button)

        edit_button = QPushButton("✏️", self)
        edit_button.setFixedSize(25, 25)
        edit_button.clicked.connect(self.toggle_edit_mode)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("❌", self)
        delete_button.setFixedSize(25, 25)
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.index))
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        # 设置消息内容编辑框
        self.content_edit = QTextEdit(self)
        self.content_edit.setReadOnly(True)
        self.content_edit.setText(self.message)
        self.content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置文本框自适应内容大小
        self.content_edit.document().contentsChanged.connect(self.adjust_text_edit_size)
        self.content_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 根据角色设置样式
        style = """
            QTextEdit {
                border-radius: 10px;
                padding: 8px;
                background-color: %s;
                border: none;
            }
        """
        if self.role == "user":
            self.content_edit.setStyleSheet(style % "rgba(200, 220, 240, 200)")
            self.setLayoutDirection(Qt.RightToLeft)
        elif self.role == "assistant":
            self.content_edit.setStyleSheet(style % "rgba(220, 220, 220, 200)")
            self.setLayoutDirection(Qt.LeftToRight)
        else:  # error
            self.content_edit.setStyleSheet(style % "rgba(255, 200, 200, 200)")
            self.setLayoutDirection(Qt.LeftToRight)

        layout.addWidget(self.content_edit)
        self.adjust_text_edit_size()

    def adjust_text_edit_size(self):
        # 获取文档大小
        doc_size = self.content_edit.document().size()
        # 设置最小文本框高度
        min_height = 40
        # 计算合适的高度（文档高度 + 一些边距）
        content_height = doc_size.height() + 20
        # 确保高度不小于最小高度
        height = max(min_height, content_height)
        # 设置固定高度
        self.content_edit.setFixedHeight(int(height))

    def toggle_edit_mode(self):
        is_readonly = self.content_edit.isReadOnly()
        self.content_edit.setReadOnly(not is_readonly)
        if is_readonly:
            # 进入编辑模式
            self.content_edit.setStyleSheet(self.content_edit.styleSheet() + "QTextEdit { border: 2px solid #4A90E2; }")
        else:
            # 退出编辑模式，保存更改
            self.content_edit.setStyleSheet(self.content_edit.styleSheet().replace("border: 2px solid #4A90E2;", ""))
            self.edit_completed.emit(self.index, self.content_edit.toPlainText())

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # 所有消息都支持编辑和删除
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(self.edit_message)
        menu.addAction(edit_action)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.index))
        menu.addAction(delete_action)
        
        # 如果有多个候选回复，添加切换选项
        if len(self.alternatives) > 0:
            switch_menu = menu.addMenu("切换候选")
            for i, _ in enumerate(self.alternatives):
                action = QAction(f"候选 {i+1}", self)
                action.triggered.connect(lambda checked, idx=i: self.switch_alternative(idx))
                switch_menu.addAction(action)
        
        menu.exec_(event.globalPos())
        
    def edit_message(self):
        self.editing = True
        self.content_edit.setReadOnly(False)
        self.content_edit.setFocus()
        self.confirm_button.show()
        self.cancel_button.show()
        # 设置文本框样式以显示可编辑状态
        self.content_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 180);
                border: 1px solid #ccc;
            }
        """)
        
    def confirm_edit(self):
        self.editing = False
        self.content_edit.setReadOnly(True)
        new_text = self.content_edit.toPlainText()
        self.edit_completed.emit(self.index, new_text)
        self.confirm_button.hide()
        self.cancel_button.hide()
        # 恢复原始样式
        self.restore_style()
        
    def cancel_edit(self):
        self.editing = False
        self.content_edit.setReadOnly(True)
        self.content_edit.setText(self.message)
        self.confirm_button.hide()
        self.cancel_button.hide()
        # 恢复原始样式
        self.restore_style()
        
    def restore_style(self):
        # 恢复原始样式
        self.content_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 5px;
            }
        """)
        
    def switch_alternative(self, alt_index):
        if 0 <= alt_index < len(self.alternatives):
            self.current_alt_index = alt_index
            self.content_edit.setText(self.alternatives[alt_index])
            self.message = self.alternatives[alt_index]
            self.edit_completed.emit(self.index, self.message)

    def add_alternative(self, text):
        self.alternatives.append(text)
