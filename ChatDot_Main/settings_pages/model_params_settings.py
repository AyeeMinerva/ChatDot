from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QSpinBox, QCheckBox, QGridLayout
from PyQt5.QtCore import Qt

class ModelParamsSettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.param_checkboxes = {} #  !!!  用于存储参数复选框的字典 !!!
        self.temp_spinbox = None #  !!!  temperature 参数调节 SpinBox !!!
        self.top_p_spinbox = None #  !!!  top_p 参数调节 SpinBox !!!
        self.max_tokens_spinbox = None #  !!!  max_tokens 参数调节 SpinBox !!!
        self.frequency_penalty_spinbox = None #  !!!  frequency_penalty 参数调节 SpinBox !!!
        self.presence_penalty_spinbox = None #  !!!  presence_penalty 参数调节 SpinBox !!!
        self.initUI()

    def initUI(self):
        layout = QGridLayout(self) #  !!!  使用 QGridLayout !!!
        row = 0

        self.temp_spinbox = QDoubleSpinBox(self, minimum=0.0, maximum=2.0, singleStep=0.1, value=0.7)
        row = self.add_parameter_row("temperature", "温度:", self.temp_spinbox, layout, row)
        self.top_p_spinbox = QDoubleSpinBox(self, minimum=0.0, maximum=1.0, singleStep=0.05, value=0.9)
        row = self.add_parameter_row("top_p", "Top P:", self.top_p_spinbox, layout, row)
        self.max_tokens_spinbox = QSpinBox(self, minimum=1, maximum=4096, singleStep=100, value=200)
        row = self.add_parameter_row("max_tokens", "最大 Token:", self.max_tokens_spinbox, layout, row)
        self.frequency_penalty_spinbox = QDoubleSpinBox(self, minimum=-2.0, maximum=2.0, singleStep=0.1, value=0.0)
        row = self.add_parameter_row("frequency_penalty", "频率惩罚:", self.frequency_penalty_spinbox, layout, row)
        self.presence_penalty_spinbox = QDoubleSpinBox(self, minimum=-2.0, maximum=2.0, singleStep=0.1, value=0.0)
        row = self.add_parameter_row("presence_penalty", "存在惩罚:", self.presence_penalty_spinbox, layout, row)

        self.setLayout(layout)


    def add_parameter_row(self, param_name, label_text, control, layout, row_index):
        label = QLabel(label_text)
        checkbox = QCheckBox() #  !!!  创建复选框 !!!
        checkbox.setChecked(False) #  !!!  默认不勾选 !!!
        self.param_checkboxes[param_name] = checkbox #  !!!  保存复选框实例 !!!

        layout.addWidget(label, row_index, 0, Qt.AlignLeft)
        layout.addWidget(control, row_index, 1)
        layout.addWidget(checkbox, row_index, 2) #  !!!  添加复选框到布局 !!!
        return row_index + 1

    def get_model_params_settings(self):
        params = {}
        if self.param_checkboxes['temperature'].isChecked():
            params['temperature'] = self.temp_spinbox.value()
        if self.param_checkboxes['top_p'].isChecked():
            params['top_p'] = self.top_p_spinbox.value()
        if self.param_checkboxes['max_tokens'].isChecked():
            params['max_tokens'] = int(self.max_tokens_spinbox.value())
        if self.param_checkboxes['frequency_penalty'].isChecked():
            params['frequency_penalty'] = self.frequency_penalty_spinbox.value()
        if self.param_checkboxes['presence_penalty'].isChecked():
            params['presence_penalty'] = self.presence_penalty_spinbox.value()
        return params