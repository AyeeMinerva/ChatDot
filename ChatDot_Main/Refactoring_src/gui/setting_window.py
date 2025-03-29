from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread

from gui.settings.floating_ball_settings import FloatingBallSettingsPage
from gui.settings.llm_connection_settings import LLMConnectionSettingsPage
from gui.settings.model_params_settings import ModelParamsSettingsPage
from gui.settings.prompt_settings import PromptSettingsPage
from gui.settings.history_settings import HistorySettingsPage
from core.bootstrap import Bootstrap
from core.global_managers.service_manager import ServiceManager  # 导入服务管理器

# 开启模型获取线程
class FetchModelsThread(QThread):
    models_fetched = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, llm_service):
        super().__init__()
        self.llm_service = llm_service

    def run(self):
        try:
            model_list = self.llm_service.fetch_models()
            self.models_fetched.emit(model_list)
        except Exception as e:
            self.error.emit(str(e))

class SettingWindow(QDialog):
    api_connected_signal = pyqtSignal()

    def __init__(self, floating_ball):
        super().__init__()
        self.floating_ball = floating_ball
        self.service_manager = None  # 初始化为 None
        self._init_services()
        self.llm_connection_settings_page = LLMConnectionSettingsPage()
        self.floating_ball_settings_page = FloatingBallSettingsPage(floating_ball)
        self.model_params_settings_page = ModelParamsSettingsPage()
        self.prompt_settings_page = PromptSettingsPage(self.service_manager)
        self.history_settings_page = HistorySettingsPage()
        self.initUI()
        self.load_user_settings()  # 打开设置时加载用户设置

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

    def initUI(self):
        self.setWindowTitle("悬浮球设置")
        self.setGeometry(300, 300, 400, 400)
        # 修改窗口标志组合方式，避免 int 类型错误
        flags = self.windowFlags()
        flags |= Qt.WindowStaysOnTopHint
        flags &= ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.addTab(self.floating_ball_settings_page, "悬浮球")
        self.tab_widget.addTab(self.llm_connection_settings_page, "LLM 连接")
        self.tab_widget.addTab(self.model_params_settings_page, "模型参数")
        self.tab_widget.addTab(self.prompt_settings_page, "对话处理")
        self.tab_widget.addTab(self.history_settings_page, "历史记录")
        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)
        self.setModal(True)

        # 连接 API 设置更改的信号
        self.llm_connection_settings_page.api_connected.connect(self.handle_api_connected)
        self.llm_connection_settings_page.model_name_changed_signal.connect(self.handle_model_name_changed)

        # 简化自动保存设置的信号连接
        for param in self.model_params_settings_page.param_checkboxes:
            self.model_params_settings_page.param_checkboxes[param].stateChanged.connect(self.auto_save_settings)

        # 连接prompt变更信号
        self.prompt_settings_page.prompt_changed.connect(self.handle_prompt_changed)

        # 连接历史记录加载信号
        self.history_settings_page.load_history_requested.connect(self.handle_load_history)

    def load_user_settings(self):
        """从核心服务加载用户设置"""
        llm_service = self.service_manager.get_service("llm_service")
        context_handle_service = self.service_manager.get_service("context_handle_service")
        chat_service = self.service_manager.get_service("chat_service")

        # 加载 API 相关设置
        api_base = llm_service.settings.get_setting('api_base')
        api_keys = llm_service.settings.get_setting('api_keys')
        model_name = llm_service.settings.get_setting('model_name')
        
        # 设置 API Base URL
        self.llm_connection_settings_page.api_base_input.setText(api_base)
        # 设置 API Keys
        self.llm_connection_settings_page.set_api_keys(api_keys)
        # 设置当前使用的模型
        self.llm_connection_settings_page.set_model(model_name)

    @pyqtSlot(str)
    def handle_model_name_changed(self, model_name):
        """处理模型名称改变信号"""
        llm_service = self.service_manager.get_service("llm_service")

        print(f"接收到模型名称改变信号，新模型名称: {model_name}")
        llm_service.update_setting("model_name", model_name)
        # 自动保存设置
        self.save_user_settings()

    def save_user_settings(self):
        """将用户设置保存到核心服务"""
        llm_service = self.service_manager.get_service("llm_service")
        context_handle_service = self.service_manager.get_service("context_handle_service")

        # 获取当前选中的 prompt 处理器文件名
        current_item = self.prompt_settings_page.prompt_list.currentItem()
        prompt_handler = current_item.text() if current_item else 'defaultPrompt'

        # 保存 API 相关设置
        llm_service.update_setting('api_base', self.llm_connection_settings_page.api_base_input.text().strip())
        llm_service.update_setting('api_keys', self.llm_connection_settings_page.api_keys)
        llm_service.update_setting('model_params', self.model_params_settings_page.get_model_params_settings())
        llm_service.update_setting('model_name', llm_service.client.get_model_name())

        # 保存 prompt 处理器设置
        context_handle_service.manager.persistence.save_current_handler(prompt_handler)

    def applySettings(self):
        """应用设置"""
        llm_service = self.service_manager.get_service("llm_service")

        llm_connection_settings = self.llm_connection_settings_page.get_llm_connection_settings()
        api_keys = llm_connection_settings.get('api_keys',[])
        api_base = llm_connection_settings.get('api_base')
        try:
            llm_service.client.set_api_config(api_keys=api_keys, api_base=api_base)
        except Exception as e:
            QMessageBox.warning(self, "API 配置错误", str(e))
            return

        model_params_settings = self.model_params_settings_page.get_model_params_settings()
        llm_service.client.set_model_params(model_params_settings)

        # 静默应用设置，不弹窗
        self.get_model_list()
        self.save_user_settings()
        # 不要使用 accept() 或 close()，让设置窗口保持打开状态

    def handle_api_connected(self, api_settings):
        """处理API连接测试"""
        llm_service = self.service_manager.get_service("llm_service")
        try:
            # 使用test_connection=True进行API测试
            llm_service.client.set_api_config(
                api_keys=api_settings['api_keys'],
                api_base=api_settings['api_base'],
                test_connection=True
            )

            # 如果测试成功，获取模型列表
            self.get_model_list()

            # 保存成功的配置
            self.save_user_settings()

        except Exception as e:
            QMessageBox.critical(self, "API 连接失败", str(e))
            self.llm_connection_settings_page.model_name_combo.clear()
            self.llm_connection_settings_page.model_name_combo.addItem("请先连接API")
            self.llm_connection_settings_page.model_name_combo.setEnabled(False)

    def get_model_list(self):
        """获取模型列表"""
        llm_service = self.service_manager.get_service("llm_service")

        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem("正在获取模型列表...")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

        model_list = llm_service.fetch_models()
        self.populate_model_dropdown(model_list)

    @pyqtSlot(list)
    def populate_model_dropdown(self, model_list):
        """填充模型下拉菜单"""
        self.llm_connection_settings_page.populate_model_dropdown(model_list)

    @pyqtSlot(str)
    def handle_fetch_models_error(self, error_message):
        QMessageBox.critical(self, "加载模型列表失败", error_message)

    def handle_api_error(self, error_message):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem(f"API 错误: {error_message}")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

    def handle_prompt_changed(self, handler_id):
        """当选择新的prompt处理器时"""
        try:
            context_service = self.service_manager.get_service("context_handle_service")
            if context_service.set_current_handler(handler_id):
                # 获取当前处理器
                current_handler = context_service.get_current_handler()
                self.floating_ball.chat_window.current_handler = current_handler
                
                # 获取处理器名称
                handler_name = getattr(current_handler, 'name', str(current_handler))
                
                # 保存设置
                self.save_user_settings()
                
                QMessageBox.information(self, "成功", f"已切换到处理器: {handler_name}")
            else:
                QMessageBox.warning(self, "错误", f"切换处理器失败: {handler_id}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换处理器时发生错误: {str(e)}")

    def auto_save_settings(self):
        """自动保存设置"""
        llm_service = self.service_manager.get_service("llm_service")

        # 获取当前设置并保存
        model_params_settings = self.model_params_settings_page.get_model_params_settings()
        llm_service.client.set_model_params(model_params_settings)
        self.save_user_settings()

    def handle_load_history(self, file_path):
        """处理历史记录加载请求"""
        chat_service = self.service_manager.get_service("chat_service")

        try:
            # 加载历史记录
            chat_service.import_history(file_path)

            # 加载历史记录到聊天窗口
            history = chat_service.get_messages()
            self.floating_ball.chat_window.load_chat_history(history)
            QMessageBox.information(self, "加载成功", "历史记录已成功加载")
            # 显示聊天窗口
            self.floating_ball.chat_window.show()
            # 关闭设置窗口
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"加载历史记录时出错：{str(e)}")