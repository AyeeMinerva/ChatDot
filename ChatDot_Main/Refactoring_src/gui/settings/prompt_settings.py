import os
import importlib.util
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt

class PromptSettingsPage(QWidget):
    prompt_changed = pyqtSignal(str)  # 修改为发送处理器ID

    def __init__(self, service_manager=None):
        super().__init__()
        self.service_manager = service_manager
        self.prompt_list = None
        self.initUI()
        self.load_prompt_handlers()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        self.prompt_list = QListWidget()
        main_layout.addWidget(self.prompt_list)
        self.prompt_list.itemClicked.connect(self.on_prompt_selected)
        self.setLayout(main_layout)

    def load_prompt_handlers(self):
        """加载所有可用的上下文处理器"""
        if not self.service_manager:
            return
            
        context_service = self.service_manager.get_service("context_handle_service")
        handlers = context_service.get_available_handlers()
        
        # 清空列表
        self.prompt_list.clear()
        
        # 添加处理器到列表
        for handler in handlers:
            # 假设handler是一个字典，包含id、name等信息
            item = QListWidgetItem(f"{handler['name']} ({handler['id']})")
            item.setData(Qt.UserRole, handler['id'])
            self.prompt_list.addItem(item)

        # 设置当前处理器
        current_handler = context_service.get_current_handler()
        if current_handler:
            # 获取处理器ID的方式取决于你的ContextHandler类的实现
            handler_id = getattr(current_handler, 'id', None)
            if handler_id:
                self.set_current_handler(handler_id)

    def set_current_handler(self, handler_id):
        """设置当前选中的处理器"""
        for i in range(self.prompt_list.count()):
            item = self.prompt_list.item(i)
            if item.data(Qt.UserRole) == handler_id:
                self.prompt_list.setCurrentItem(item)
                break

    def on_prompt_selected(self, item):
        """当选择prompt时"""
        handler_id = item.data(Qt.UserRole)
        self.prompt_changed.emit(handler_id)