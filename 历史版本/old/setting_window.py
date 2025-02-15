from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QMessageBox, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QLabel, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot #  !!! 导入 pyqtSlot !!!

from settings_pages.floating_ball_settings import FloatingBallSettingsPage
from settings_pages.llm_connection_settings import LLMConnectionSettingsPage
from settings_pages.model_params_settings import ModelParamsSettingsPage

from llm_client import LLMClient #  !!! 确保使用相对路径导入 !!!
from llm_interaction import LLMModelListThread #  !!! 确保使用相对路径导入 !!!


class SettingWindow(QDialog):
    api_connected_signal = pyqtSignal() #  !!!  新增信号，用于通知 API 连接成功 !!!

    def __init__(self, floating_ball):
        super().__init__()
        self.floating_ball = floating_ball
        self.llm_client = floating_ball.chat_window.llm_client #  !!!  直接获取 ChatWindow 的 llm_client 实例 !!!
        self.llm_connection_settings_page = LLMConnectionSettingsPage()
        self.floating_ball_settings_page = FloatingBallSettingsPage(floating_ball)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("悬浮球设置")
        self.setGeometry(300, 300, 400, 400) #  !!!  调整窗口高度，容纳模型参数设置 !!!
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget(self)

        self.tab_widget.addTab(self.floating_ball_settings_page, "悬浮球")
        self.tab_widget.addTab(self.llm_connection_settings_page, "LLM 连接")

        #  !!!  添加模型参数设置页面  !!!
        self.model_params_settings_page = ModelParamsSettingsPage() #  !!!  创建模型参数设置页面实例 !!!
        self.tab_widget.addTab(self.model_params_settings_page, "模型参数") #  !!!  添加到 TabWidget !!!


        self.tab_widget.addTab(self.llm_connection_settings_page, "LLM 连接") # LLM 连接设置页

        main_layout.addWidget(self.tab_widget)

        # 按钮布局
        button_layout = QHBoxLayout()
        apply_button = QPushButton("应用", self)
        apply_button.clicked.connect(self.applySettings)
        cancel_button = QPushButton("取消", self)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setModal(True)

        self.llm_connection_settings_page.api_connected.connect(self.handle_api_connected)
        #  !!!  连接模型名称改变信号到槽函数  !!!
        self.llm_connection_settings_page.model_name_changed_signal.connect(self.handle_model_name_changed) #  !!!  新增代码 !!!


    def applySettings(self):
        # 获取 LLM 连接设置页面的设置数据 (API Key, API Base URL)
        llm_connection_settings = self.llm_connection_settings_page.get_llm_connection_settings()
        print("LLM 连接设置:", llm_connection_settings)

        # 获取 模型参数设置页面的设置数据
        model_params_settings = self.model_params_settings_page.get_model_params_settings() #  !!!  获取模型参数设置 !!!
        print("模型参数设置:", model_params_settings) #  !!!  打印模型参数设置 !!!


        #  !!!  应用 LLM 连接设置  !!!
        api_key = llm_connection_settings.get('api_key')
        api_base = llm_connection_settings.get('api_base')
        self.llm_client.set_api_config(api_key=api_key, api_base=api_base) #  !!!  应用 API 配置 !!!


        #  !!!  应用模型参数设置  !!!
        self.llm_client.set_model_params(model_params_settings) #  !!!  应用模型参数设置 !!!


        QMessageBox.information(self, "设置", "设置已应用！(当前设置仅临时生效，未保存)")
        self.accept()


    def handle_api_connected(self, api_settings):
        api_key = api_settings.get('api_key')
        api_base = api_settings.get('api_base')

        try:
            self.llm_client.set_api_config(api_key=api_key, api_base=api_base)
            QMessageBox.information(self, "API 连接", "API 连接成功！")
            self.get_model_list()
            self.api_connected_signal.emit() #  !!!  发送 API 连接成功信号 !!!
        except ValueError as e:
            QMessageBox.warning(self, "API 配置错误", str(e))
            self.handle_api_error(str(e))
        except RuntimeError as e:
            QMessageBox.critical(self, "API 连接失败", f"连接失败，请检查API配置和网络。\n错误信息: {e}")
            self.handle_api_error(str(e))


    def get_model_list(self):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem("正在获取模型列表...")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

        self.model_list_thread = LLMModelListThread(self.llm_client)
        self.model_list_thread.models_fetched.connect(self.populate_model_dropdown)
        self.model_list_thread.error_fetching_models.connect(self.handle_model_list_error)
        self.model_list_thread.start()


    def populate_model_dropdown(self, model_list):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItems(model_list)
        if model_list:
            self.llm_connection_settings_page.model_name_combo.setCurrentIndex(0)
            default_model_name = model_list[0] #  !!!  默认选择第一个模型 !!!
            self.llm_client.set_model_name(default_model_name) #  !!!  设置默认模型到 llm_client !!!
        else:
            self.llm_connection_settings_page.model_name_combo.addItem("模型列表为空")
        self.llm_connection_settings_page.model_name_combo.setEnabled(True)

    @pyqtSlot(str) #  !!!  pyqtSlot 装饰器，指定槽函数接收 str 类型参数 (model_name) !!!
    def handle_model_name_changed(self, model_name): #  !!!  新的槽函数，处理模型名称改变信号 !!!
        print(f"接收到模型名称改变信号，新模型名称: {model_name}") #  !!!  调试输出 !!!
        self.llm_client.set_model_name(model_name) #  !!!  更新 LLMClient 中的模型名称 !!!


    def handle_model_list_error(self, error_message):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem(f"获取模型列表失败: {error_message}")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

    def handle_api_error(self, error_message):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem(f"API 错误: {error_message}")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)