import os
import shutil
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame, 
                            QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

class HistoryFileItem(QFrame):
    """历史文件项组件，显示一个历史文件及其操作按钮"""
    delete_requested = pyqtSignal(str)  # 请求删除文件的信号
    load_requested = pyqtSignal(str)    # 请求加载文件的信号
    
    def __init__(self, file_path, file_name, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = file_name
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("QFrame { border: 1px solid #cccccc; border-radius: 3px; background-color: #f9f9f9; }")
        
        # 创建水平布局
        layout = QHBoxLayout(self)
        
        # 文件名标签
        self.file_label = QLabel(file_name)
        self.file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.file_label)
        
        # 加载按钮
        self.load_btn = QPushButton("载入")
        self.load_btn.setStyleSheet("QPushButton { min-width: 60px; }")
        self.load_btn.clicked.connect(self.emit_load_signal)
        layout.addWidget(self.load_btn)
        
        # 删除按钮
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setStyleSheet("QPushButton { min-width: 60px; }")
        self.delete_btn.clicked.connect(self.emit_delete_signal)
        layout.addWidget(self.delete_btn)
        
        self.setLayout(layout)
    
    def emit_delete_signal(self):
        self.delete_requested.emit(self.file_path)
    
    def emit_load_signal(self):
        self.load_requested.emit(self.file_path)

class HistorySettingsPage(QWidget):
    """历史记录设置页面，显示和管理聊天历史文件"""
    load_history_requested = pyqtSignal(str)  # 请求加载历史记录的信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_dir = os.path.join(os.getcwd(), "ChatDot_Main", "history")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("聊天历史记录")
        title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title_label)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新历史记录列表")
        refresh_button.clicked.connect(self.load_history_files)
        layout.addWidget(refresh_button)
        
        # 滚动区域用于显示文件列表
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        # 加载历史文件
        self.load_history_files()
        
    def load_history_files(self):
        # 清空原有列表
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 确保目录存在
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
        
        # 加载目录下所有json文件
        files = [f for f in os.listdir(self.history_dir) if f.endswith('.json')]
        files.sort(reverse=True)  # 最新的文件在前面
        
        if not files:
            empty_label = QLabel("没有找到历史记录文件")
            empty_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
            return
            
        # 添加文件项到滚动区域
        for file_name in files:
            file_path = os.path.join(self.history_dir, file_name)
            file_item = HistoryFileItem(file_path, file_name)
            file_item.delete_requested.connect(self.delete_history_file)
            file_item.load_requested.connect(self.load_history_file)
            self.scroll_layout.addWidget(file_item)
    
    def delete_history_file(self, file_path):
        """删除历史记录文件"""
        reply = QMessageBox.question(
            self, 
            '确认删除', 
            f"确定要删除此历史记录文件吗？\n{os.path.basename(file_path)}",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "删除成功", "历史记录文件已删除")
                self.load_history_files()  # 刷新列表
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"删除文件时出错：{str(e)}")
    
    def load_history_file(self, file_path):
        """加载历史记录文件"""
        self.load_history_requested.emit(file_path)
