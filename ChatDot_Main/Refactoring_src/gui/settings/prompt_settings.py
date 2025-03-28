import os
import importlib.util
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal

class PromptSettingsPage(QWidget):
    prompt_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.prompt_list = None
        self.initUI()
        self.load_prompt_handlers()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Prompt List
        self.prompt_list = QListWidget()
        main_layout.addWidget(self.prompt_list)

        # Connect item selection
        self.prompt_list.itemClicked.connect(self.on_prompt_selected)

        self.setLayout(main_layout)

    def load_prompt_handlers(self):
        """加载所有可用的上下文处理器"""
        handlers_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "chat", "context_handle", "providers")
        if not os.path.exists(handlers_dir):
            return

        for file in os.listdir(handlers_dir):
            if file.endswith('.py') and not file.startswith('__'):
                handler_name = file[:-3]
                try:
                    # 动态加载模块
                    spec = importlib.util.spec_from_file_location(
                        handler_name,
                        os.path.join(handlers_dir, file)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 注册处理器
                    if hasattr(module, 'ContextHandler'):
                        item = QListWidgetItem(handler_name)
                        self.prompt_list.addItem(item)
                except Exception as e:
                    print(f"加载处理器 {handler_name} 失败: {str(e)}")

    def set_current_handler(self, handler_name):
        """设置当前选中的处理器"""
        for i in range(self.prompt_list.count()):
            item = self.prompt_list.item(i)
            if item.text() == handler_name:
                self.prompt_list.setCurrentItem(item)
                break

    def on_prompt_selected(self, item):
        """当选择 prompt 时"""
        handler_name = item.text()
        # 构建完整的文件路径
        handlers_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "chat", "context_handle", "providers")
        file_path = os.path.join(handlers_dir, handler_name + '.py')
        
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(handler_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 检查模块是否包含 ContextHandler 类
            if hasattr(module, 'ContextHandler'):
                handler_class = module.ContextHandler
                # 创建处理器实例
                handler = handler_class()
                # 发送信号
                self.prompt_changed.emit(handler)
            else:
                print(f"模块 {handler_name} 不包含 ContextHandler 类")
        except Exception as e:
            print(f"加载处理器 {handler_name} 失败: {str(e)}")