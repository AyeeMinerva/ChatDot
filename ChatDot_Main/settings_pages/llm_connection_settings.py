from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox, QMessageBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot #  !!! 导入 pyqtSlot !!!

class LLMConnectionSettingsPage(QWidget):
    api_connected = pyqtSignal(dict)
    model_name_changed_signal = pyqtSignal(str) #  !!!  新增信号，用于传递模型名称改变事件 !!!

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # API Base URL
        self.api_base_label = QLabel("API Base URL:", self)
        self.api_base_input = QLineEdit(self)
        layout.addWidget(self.api_base_label)
        layout.addWidget(self.api_base_input)

        # API Key
        self.api_key_label = QLabel("API Key:", self)
        self.api_key_input = QLineEdit(self)
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)

        # 模型选择
        self.model_name_label = QLabel("模型:", self)
        self.model_name_combo = QComboBox(self)
        self.model_name_combo.addItem("请先连接API") # 初始提示
        self.model_name_combo.setEnabled(False) # 初始禁用
        layout.addWidget(self.model_name_label)
        layout.addWidget(self.model_name_combo)

        #  !!!  连接下拉框的 currentIndexChanged 信号到槽函数  !!!
        self.model_name_combo.currentIndexChanged.connect(self.on_model_name_changed) #  !!!  新增代码 !!!


        # 连接按钮
        connection_layout = QHBoxLayout()
        self.connect_button = QPushButton("连接", self)
        self.connect_button.clicked.connect(self.connect_api)
        connection_layout.addWidget(self.connect_button)
        layout.addLayout(connection_layout)

        self.setLayout(layout)


    def connect_api(self):
        api_key = self.api_key_input.text().strip()
        api_base = self.api_base_input.text().strip()

        if not api_key or not api_base:
            QMessageBox.warning(self, "API 配置", "API Base URL 和 API Key 不能为空。")
            return

        api_settings = {
            'api_key': api_key,
            'api_base': api_base
        }
        self.api_connected.emit(api_settings) # 发射信号，传递API设置

    @pyqtSlot(int) #  !!!  pyqtSlot 装饰器，指定槽函数接收 int 类型参数 (currentIndex) !!!
    def on_model_name_changed(self, index): #  !!!  新的槽函数，处理模型下拉框选择变化事件 !!!
        model_name = self.model_name_combo.itemText(index) # 获取当前选中的模型名称

        #  !!!  新增模型名称校验 !!!
        if not model_name or model_name == "请先连接API" or model_name == "正在获取模型列表..." or model_name == "API 配置错误" or model_name == "API 连接失败" or model_name == "模型列表为空" or model_name.startswith("获取模型列表失败"):
            print(f"模型下拉框选择了无效的模型名称: {model_name}，忽略模型名称更新信号。") #  !!!  调试输出 !!!
            return #  !!!  如果模型名称无效，直接返回，不发射信号 !!!
        #  !!!  校验结束 !!!

        print(f"模型下拉框选择改变，新模型名称: {model_name}") #  !!!  调试输出 !!!
        self.model_name_changed_signal.emit(model_name) #  !!!  发射模型名称改变信号，传递新的模型名称 !!!


    def get_llm_connection_settings(self):
        return {
            'api_base': self.api_base_input.text().strip(),
            'api_key': self.api_key_input.text().strip()
        }