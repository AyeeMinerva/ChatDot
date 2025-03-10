from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

from gui.settings.floating_ball_settings import FloatingBallSettingsPage
from gui.settings.llm_connection_settings import LLMConnectionSettingsPage
from gui.settings.model_params_settings import ModelParamsSettingsPage

from client.llm_client import LLMClient
from client.llm_interaction import LLMModelListThread
from persistence.settings_persistence import load_settings, save_settings  # 新增导入

class SettingWindow(QDialog):
    api_connected_signal = pyqtSignal()

    def __init__(self, floating_ball):
        super().__init__()
        self.floating_ball = floating_ball
        self.llm_client = floating_ball.chat_window.llm_client
        self.llm_connection_settings_page = LLMConnectionSettingsPage()
        self.floating_ball_settings_page = FloatingBallSettingsPage(floating_ball)
        self.model_params_settings_page = ModelParamsSettingsPage()
        self.initUI()
        self.load_user_settings()  # 打开设置时加载用户设置

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
        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)
        self.setModal(True)

        # 连接 API 设置更改的信号
        self.llm_connection_settings_page.api_connected.connect(self.handle_api_connected)
        self.llm_connection_settings_page.model_name_changed_signal.connect(self.handle_model_name_changed)

        # 自动保存设置的信号连接
        self.model_params_settings_page.param_checkboxes['temperature'].stateChanged.connect(self.auto_save_settings)
        self.model_params_settings_page.param_checkboxes['top_p'].stateChanged.connect(self.auto_save_settings)
        self.model_params_settings_page.param_checkboxes['max_tokens'].stateChanged.connect(self.auto_save_settings)
        self.model_params_settings_page.param_checkboxes['frequency_penalty'].stateChanged.connect(self.auto_save_settings)
        self.model_params_settings_page.param_checkboxes['presence_penalty'].stateChanged.connect(self.auto_save_settings)

    def load_user_settings(self):
        settings = load_settings()
        # 加载 API 相关设置
        api_base = settings.get('api_base', '')
        api_keys = settings.get('api_keys', [])
        model_name = settings.get('model_name', '')
        model_list = settings.get('model_list', [])
        
        # 设置 API Base URL
        self.llm_connection_settings_page.api_base_input.setText(api_base)
        # 设置 API Keys
        self.llm_connection_settings_page.set_api_keys(api_keys)
        
        # 如果有保存的模型列表和选中模型，直接加载
        if model_list:
            self.llm_connection_settings_page.model_name_combo.clear()
            self.llm_connection_settings_page.model_name_combo.addItems(model_list)
            if model_name in model_list:
                index = model_list.index(model_name)
                self.llm_connection_settings_page.model_name_combo.setCurrentIndex(index)
                self.llm_client.set_model_name(model_name)
        
        # 如果有API配置，设置API配置
        if api_keys and api_base:
            try:
                self.llm_client.set_api_config(api_keys=api_keys, api_base=api_base, test_connection=False)
                self.llm_connection_settings_page.model_name_combo.setEnabled(True)
            except Exception as e:
                print(f"设置API配置失败: {e}")
        
        # 加载模型参数设置
        model_params = settings.get('model_params', {})
        if model_params:
            if 'temperature' in model_params:
                self.model_params_settings_page.temp_spinbox.setValue(model_params['temperature'])
                self.model_params_settings_page.param_checkboxes['temperature'].setChecked(True)
            if 'top_p' in model_params:
                self.model_params_settings_page.top_p_spinbox.setValue(model_params['top_p'])
                self.model_params_settings_page.param_checkboxes['top_p'].setChecked(True)
            if 'max_tokens' in model_params:
                self.model_params_settings_page.max_tokens_spinbox.setValue(model_params['max_tokens'])
                self.model_params_settings_page.param_checkboxes['max_tokens'].setChecked(True)
            if 'frequency_penalty' in model_params:
                self.model_params_settings_page.frequency_penalty_spinbox.setValue(model_params['frequency_penalty'])
                self.model_params_settings_page.param_checkboxes['frequency_penalty'].setChecked(True)
            if 'presence_penalty' in model_params:
                self.model_params_settings_page.presence_penalty_spinbox.setValue(model_params['presence_penalty'])
                self.model_params_settings_page.param_checkboxes['presence_penalty'].setChecked(True)

    def save_user_settings(self):
        settings = {
            'api_base': self.llm_connection_settings_page.api_base_input.text().strip(),
            'api_keys': self.llm_connection_settings_page.api_keys,
            'model_params': self.model_params_settings_page.get_model_params_settings(),
            'model_name': self.llm_client.get_model_name(),
            'model_list': [self.llm_connection_settings_page.model_name_combo.itemText(i) 
                          for i in range(self.llm_connection_settings_page.model_name_combo.count())
                          if self.llm_connection_settings_page.model_name_combo.itemText(i) not in 
                          ["请先连接API", "正在获取模型列表...", "模型列表为空"]]
        }
        save_settings(settings)

    def applySettings(self):
        llm_connection_settings = self.llm_connection_settings_page.get_llm_connection_settings()
        api_key = llm_connection_settings.get('api_keys',[])
        api_base = llm_connection_settings.get('api_base')
        try:
            self.llm_client.set_api_config(api_key=api_key, api_base=api_base)
        except Exception as e:
            QMessageBox.warning(self, "API 配置错误", str(e))
            return

        model_params_settings = self.model_params_settings_page.get_model_params_settings()
        self.llm_client.set_model_params(model_params_settings)
        
        # 静默应用设置，不弹窗
        self.get_model_list()
        self.save_user_settings()
        # 不要使用 accept() 或 close()，让设置窗口保持打开状态

    def handle_api_connected(self, api_settings):
        """处理API连接测试"""
        try:
            # 使用test_connection=True进行API测试
            self.llm_client.set_api_config(
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
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem("正在获取模型列表...")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

        self.model_list_thread = LLMModelListThread(self.llm_client)
        self.model_list_thread.models_fetched.connect(self.populate_model_dropdown)
        self.model_list_thread.error_fetching_models.connect(self.handle_model_list_error)
        self.model_list_thread.start()

    def populate_model_dropdown(self, model_list):
        # 过滤并清理模型名称，移除 "models/" 前缀，并排除空值
        cleaned_model_list = []
        for model in model_list:
            new_model = model
            if new_model.startswith("models/"):
                new_model = new_model[len("models/"):]
            if new_model.strip():
                cleaned_model_list.append(new_model)
        self.llm_connection_settings_page.model_name_combo.clear()
        if cleaned_model_list:
            self.llm_connection_settings_page.model_name_combo.addItems(cleaned_model_list)
            self.llm_connection_settings_page.model_name_combo.setCurrentIndex(0)
            default_model_name = cleaned_model_list[0]
            self.llm_client.set_model_name(default_model_name)
        else:
            self.llm_connection_settings_page.model_name_combo.addItem("模型列表为空")
        self.llm_connection_settings_page.model_name_combo.setEnabled(True)

    @pyqtSlot(str)
    def handle_model_name_changed(self, model_name):
        print(f"接收到模型名称改变信号，新模型名称: {model_name}")
        self.llm_client.set_model_name(model_name)

    def handle_model_list_error(self, error_message):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem(f"获取模型列表失败: {error_message}")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

    def handle_api_error(self, error_message):
        self.llm_connection_settings_page.model_name_combo.clear()
        self.llm_connection_settings_page.model_name_combo.addItem(f"API 错误: {error_message}")
        self.llm_connection_settings_page.model_name_combo.setEnabled(False)

    def auto_save_settings(self):
        # 获取当前设置并保存
        model_params_settings = self.model_params_settings_page.get_model_params_settings()
        self.llm_client.set_model_params(model_params_settings)
        self.save_user_settings()
