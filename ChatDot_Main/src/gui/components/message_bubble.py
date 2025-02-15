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
        layout = QHBoxLayout()
        if self.role == "assistant":
            layout.addStretch()
            
        bubble_widget = QWidget()
        bubble_widget.setObjectName("messageBubble")
        bubble_layout = QVBoxLayout(bubble_widget)
        
        # 消息内容
        self.content_edit = QTextEdit()
        self.content_edit.setReadOnly(True)
        self.content_edit.setText(self.message)
        self.content_edit.setMinimumWidth(200)
        self.content_edit.setMaximumWidth(600)
        # 设置自动调整高度
        self.content_edit.document().contentsChanged.connect(self.adjust_height)
        self.content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 设置样式
        if self.role == "user":
            bubble_widget.setStyleSheet("""
                #messageBubble {
                    background-color: #95EC69;
                    border-radius: 10px;
                    padding: 10px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    padding: 5px;
                }
            """)
        else:
            bubble_widget.setStyleSheet("""
                #messageBubble {
                    background-color: #FFFFFF;
                    border-radius: 10px;
                    padding: 10px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    padding: 5px;
                }
            """)
            
        bubble_layout.addWidget(self.content_edit)
        
        # 编辑按钮布局
        self.edit_buttons = QHBoxLayout()
        self.confirm_button = QPushButton("确认")
        self.cancel_button = QPushButton("取消")
        self.confirm_button.clicked.connect(self.confirm_edit)
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.edit_buttons.addWidget(self.confirm_button)
        self.edit_buttons.addWidget(self.cancel_button)
        self.confirm_button.hide()
        self.cancel_button.hide()
        bubble_layout.addLayout(self.edit_buttons)
        
        layout.addWidget(bubble_widget)
        if self.role == "user":
            layout.addStretch()
        self.setLayout(layout)

    def adjust_height(self):
        # 自动调整文本框高度，将 float 转为 int
        doc_height = int(self.content_edit.document().size().height())
        self.content_edit.setMinimumHeight(doc_height + 10)
        self.content_edit.setMaximumHeight(doc_height + 10)
        
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
