from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                            QHBoxLayout, QComboBox, QMessageBox, QListWidget, QInputDialog,
                            QProgressDialog)
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt

from core.global_managers.service_manager import ServiceManager  # 导入服务管理器

class LLMConnectionSettingsPage(QWidget):
    api_connected = pyqtSignal(dict)
    model_name_changed_signal = pyqtSignal(str)  # 新增信号，用于传递模型名称改变事件

    def __init__(self):
        super().__init__()
        self.service_manager = ServiceManager()  # 获取服务管理器实例
        self.api_keys = []  # 存储多个API Keys
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # API Base URL
        self.api_base_label = QLabel("API Base URL:", self)
        self.api_base_input = QLineEdit(self)
        layout.addWidget(self.api_base_label)
        layout.addWidget(self.api_base_input)

        # API Keys List
        self.api_keys_label = QLabel("API Keys:", self)
        layout.addWidget(self.api_keys_label)

        self.api_keys_list = QListWidget(self)
        layout.addWidget(self.api_keys_list)

        # API Keys 管理按钮
        keys_buttons_layout = QHBoxLayout()
        self.add_key_button = QPushButton("添加Key", self)
        self.remove_key_button = QPushButton("删除Key", self)

        self.add_key_button.clicked.connect(self.add_api_key)
        self.remove_key_button.clicked.connect(self.remove_api_key)

        keys_buttons_layout.addWidget(self.add_key_button)
        keys_buttons_layout.addWidget(self.remove_key_button)
        layout.addLayout(keys_buttons_layout)

        # 模型选择
        self.model_name_label = QLabel("模型:", self)
        self.model_name_combo = QComboBox(self)
        self.model_name_combo.addItem("请先连接API")  # 初始提示
        self.model_name_combo.setEnabled(False)  # 初始禁用
        layout.addWidget(self.model_name_label)
        layout.addWidget(self.model_name_combo)

        # 连接下拉框的 currentIndexChanged 信号到槽函数
        self.model_name_combo.currentIndexChanged.connect(self.on_model_name_changed)

        # 连接按钮
        connection_layout = QHBoxLayout()
        self.connect_button = QPushButton("获取模型列表", self)
        self.manual_button = QPushButton("手动输入模型", self)
        self.connect_button.clicked.connect(self.test_api_connection)
        self.manual_button.clicked.connect(self.manual_input_model)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.manual_button)
        layout.addLayout(connection_layout)

        self.setLayout(layout)

    def test_api_connection(self):
        """获取可用的模型列表"""
        api_base = self.api_base_input.text().strip()
        api_keys = self.api_keys

        if not api_keys or not api_base:
            QMessageBox.warning(self, "API 配置", "API Base URL 和至少一个 API Key 不能为空。")
            return

        # 创建进度对话框
        progress = QProgressDialog("正在获取模型列表...", "取消", 0, 1, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("获取模型列表")
        progress.setAutoClose(True)
        progress.show()

        try:
            # 获取 LLM 服务
            llm_service = self.service_manager.get_service("llm_service")

            # 设置 API 配置
            try:
                llm_service.adapter.set_api_config(api_keys=api_keys, api_base=api_base, test_connection=True)
            except Exception as e:
                QMessageBox.critical(self, "API 连接失败", str(e))
                self.model_name_combo.clear()
                self.model_name_combo.addItem("请先连接API")
                self.model_name_combo.setEnabled(False)
                return

            # 获取模型列表
            model_list = llm_service.fetch_models()
            self.populate_model_dropdown(model_list)

            # 发出连接信号，保存设置
            self.api_connected.emit({
                'api_keys': api_keys,
                'api_base': api_base
            })

        except KeyError:
            QMessageBox.critical(self, "错误", "LLM 服务未注册")
        except Exception as e:
            QMessageBox.warning(self, "获取失败", f"获取模型列表失败：{str(e)}\n您可以点击'手动输入模型'按钮来指定模型。")
        finally:
            progress.close()

    def manual_input_model(self):
        """手动输入模型名称"""
        model_name, ok = QInputDialog.getText(self, "手动输入", "请输入模型名称:", QLineEdit.Normal)
        if ok and model_name.strip():
            self.model_name_combo.clear()
            self.model_name_combo.addItem(model_name.strip())
            self.model_name_combo.setEnabled(True)
            # 触发模型选择变更
            self.on_model_name_changed(0)
            # 发出API连接信号以保存设置
            self.api_connected.emit({
                'api_keys': self.api_keys,
                'api_base': self.api_base_input.text().strip()
            })

    @pyqtSlot(int)
    def on_model_name_changed(self, index):
        model_name = self.model_name_combo.itemText(index).strip()
        # 如果为提示项或空值，则不发出更新信号
        disallowed = {"请先连接API", "正在获取模型列表...", "API 配置错误", "API 连接失败", "模型列表为空"}
        if model_name in disallowed or not model_name:
            print(f"下拉框选中无效模型名: '{model_name}'，忽略更新信号。")
            return
        # 如果模型名称以 "models/" 开头，去除该前缀
        if model_name.startswith("models/"):
            model_name = model_name[len("models/"):]
        if not model_name:
            print("去除前缀后模型名称为空，忽略更新信号。")
            return
        print(f"模型下拉框选择改变，新模型名称: {model_name}")
        self.model_name_changed_signal.emit(model_name)

        # 获取 LLM 服务并更新模型名称
        llm_service = self.service_manager.get_service("llm_service")
        llm_service.update_setting("model_name", model_name)

    def add_api_key(self):
        key, ok = QInputDialog.getText(self, "添加API Key", "请输入API Key:", QLineEdit.Normal)
        if ok and key.strip():
            self.api_keys.append(key.strip())
            # 显示时只显示前8位
            self.api_keys_list.addItem(f"{key[:8]}...")

    def remove_api_key(self):
        current_row = self.api_keys_list.currentRow()
        if current_row >= 0:
            self.api_keys_list.takeItem(current_row)
            self.api_keys.pop(current_row)

    def get_llm_connection_settings(self):
        return {
            'api_base': self.api_base_input.text().strip(),
            'api_keys': self.api_keys
        }

    def set_api_keys(self, keys):
        """设置API Keys并更新显示"""
        self.api_keys = []
        self.api_keys_list.clear()
        for key in keys:
            self.api_keys.append(key)
            self.api_keys_list.addItem(f"{key[:8]}...")

    def populate_model_dropdown(self, model_list):
        """填充模型下拉菜单"""
        current_model = self.model_name_combo.currentText()
        self.model_name_combo.blockSignals(True)

        cleaned_model_list = []
        for model in model_list:
            new_model = model.replace("models/", "") if model.startswith("models/") else model
            if new_model.strip():
                cleaned_model_list.append(new_model)

        self.model_name_combo.clear()
        if cleaned_model_list:
            self.model_name_combo.addItems(cleaned_model_list)
            # 保持当前选中的模型
            if current_model and current_model in cleaned_model_list:
                self.model_name_combo.setCurrentText(current_model)
        else:
            self.model_name_combo.addItem("模型列表为空")

        self.model_name_combo.setEnabled(True)
        self.model_name_combo.blockSignals(False)

    def set_model(self, model_name):
        """设置当前模型"""
        if not model_name:
            return
            
        self.model_name_combo.blockSignals(True)
        current_items = [self.model_name_combo.itemText(i) for i in range(self.model_name_combo.count())]
        
        if model_name not in current_items:
            self.model_name_combo.clear()
            self.model_name_combo.addItem(model_name)
        
        self.model_name_combo.setCurrentText(model_name)
        self.model_name_combo.setEnabled(True)
        self.model_name_combo.blockSignals(False)