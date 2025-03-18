from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton, 
                           QLabel, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal
import os
import importlib.util
from utils.path_utils import get_project_root

class PromptSettingsPage(QWidget):
    """提示词设置页面"""
    
    prompt_changed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.prompts_dir = os.path.join(get_project_root(), "src", "Prompts")
        self.current_handler = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 处理器列表
        self.prompt_list = QListWidget()
        self.prompt_list.currentItemChanged.connect(self.on_handler_selected)
        layout.addWidget(self.prompt_list)
        
        # 处理器信息显示
        self.info_text = QLabel()
        self.info_text.setWordWrap(True)
        layout.addWidget(self.info_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确认按钮
        self.confirm_btn = QPushButton("确认选择")
        self.confirm_btn.clicked.connect(self.confirm_selection)
        self.confirm_btn.setEnabled(False)  # 初始状态禁用
        button_layout.addWidget(self.confirm_btn)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_handlers)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # 加载处理器列表
        self.load_handlers()
        
    def load_handlers(self):
        """加载所有处理器"""
        self.prompt_list.clear()
        if os.path.exists(self.prompts_dir):
            for file in os.listdir(self.prompts_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    self.prompt_list.addItem(file)
                    
    def on_handler_selected(self, current, previous):
        """处理器选择变更"""
        if not current:
            self.confirm_btn.setEnabled(False)
            self.info_text.clear()
            return
            
        try:
            # 导入处理器
            module_path = os.path.join(self.prompts_dir, current.text())
            spec = importlib.util.spec_from_file_location("prompt_handler", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 实例化处理器
            handler_class = getattr(module, "PromptHandler")
            self.current_handler = handler_class()
            
            # 更新信息显示
            info = self.current_handler.get_prompt_info()
            info_text = (
                f"名称: {info.get('name', '未命名')}\n"
                f"描述: {info.get('description', '无描述')}\n"
                f"版本: {info.get('version', '未知')}\n"
                f"作者: {info.get('author', '未知')}"
            )
            self.info_text.setText(info_text)
            
            # 启用确认按钮
            self.confirm_btn.setEnabled(True)
            
        except Exception as e:
            self.current_handler = None
            self.confirm_btn.setEnabled(False)
            self.info_text.clear()
            QMessageBox.warning(self, "加载失败", f"加载处理器失败: {str(e)}")
            
    def confirm_selection(self):
        """确认选择当前处理器"""
        if self.current_handler:
            self.prompt_changed.emit(self.current_handler)
            QMessageBox.information(self, "提示", "提示词处理器设置已更新")
            
    def set_current_handler(self, handler_name):
        """设置当前选中的处理器"""
        if not handler_name:
            return
            
        # 遍历列表查找匹配的处理器
        for i in range(self.prompt_list.count()):
            item = self.prompt_list.item(i)
            if item.text() == handler_name:
                self.prompt_list.setCurrentItem(item)
                # 同时触发处理器的初始化
                self.on_handler_selected(item, None)
                break