from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QSpinBox, QCheckBox, QGridLayout, QToolTip
from PyQt5.QtCore import Qt

class ModelParamsSettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.param_checkboxes = {}  # 用于存储参数复选框的字典
        self.temp_spinbox = None  # temperature 参数调节 SpinBox
        self.top_p_spinbox = None  # top_p 参数调节 SpinBox
        self.max_tokens_spinbox = None  # max_tokens 参数调节 SpinBox
        self.frequency_penalty_spinbox = None  # frequency_penalty 参数调节 SpinBox
        self.presence_penalty_spinbox = None  # presence_penalty 参数调节 SpinBox
        self.stream_checkbox = None  # stream 参数的复选框
        self.initUI()

    def initUI(self):
        layout = QGridLayout(self)  # 使用 QGridLayout
        row = 0

        self.temp_spinbox = QDoubleSpinBox(self, minimum=0.0, maximum=2.0, singleStep=0.1, value=0.7)
        row = self.add_parameter_row("temperature", "温度:", self.temp_spinbox, layout, row, 
                                    tooltip="控制生成文本的随机性，较高的值会使输出更加随机")
        
        self.top_p_spinbox = QDoubleSpinBox(self, minimum=0.0, maximum=1.0, singleStep=0.05, value=0.9)
        row = self.add_parameter_row("top_p", "Top P:", self.top_p_spinbox, layout, row,
                                    tooltip="控制模型考虑的词汇范围，较低的值会让模型更加确定")
        
        self.max_tokens_spinbox = QSpinBox(self, minimum=1, maximum=4096, singleStep=100, value=200)
        row = self.add_parameter_row("max_tokens", "最大 Token:", self.max_tokens_spinbox, layout, row,
                                    tooltip="限制模型生成的最大Token数量")
        
        self.frequency_penalty_spinbox = QDoubleSpinBox(self, minimum=-2.0, maximum=2.0, singleStep=0.1, value=0.0)
        row = self.add_parameter_row("frequency_penalty", "频率惩罚:", self.frequency_penalty_spinbox, layout, row,
                                    tooltip="降低模型重复使用相同词汇的可能性")
        
        self.presence_penalty_spinbox = QDoubleSpinBox(self, minimum=-2.0, maximum=2.0, singleStep=0.1, value=0.0)
        row = self.add_parameter_row("presence_penalty", "存在惩罚:", self.presence_penalty_spinbox, layout, row,
                                    tooltip="降低模型重复讨论相同话题的可能性")
        
        # 添加stream参数控制
        self.stream_checkbox = QCheckBox(self)
        self.stream_checkbox.setChecked(True)  # 默认启用
        row = self.add_parameter_row("stream", "启用流式输出:", self.stream_checkbox, layout, row,
                                    tooltip="启用后可实时看到模型生成的内容，关闭后将在生成完成后一次性显示")
        
        #layout.addStretch()
        self.setLayout(layout)

    def add_parameter_row(self, param_name, label_text, control, layout, row_index, tooltip=None):
        label = QLabel(label_text)
        if tooltip:
            label.setToolTip(tooltip)
            control.setToolTip(tooltip)
        
        # 如果控件是复选框，则不需要额外的使能复选框
        if isinstance(control, QCheckBox):
            layout.addWidget(label, row_index, 0, Qt.AlignLeft)
            layout.addWidget(control, row_index, 1)
            self.param_checkboxes[param_name] = control
        else:
            checkbox = QCheckBox()  # 创建复选框
            checkbox.setChecked(False)  # 默认不勾选
            self.param_checkboxes[param_name] = checkbox  # 保存复选框实例
            
            layout.addWidget(label, row_index, 0, Qt.AlignLeft)
            layout.addWidget(control, row_index, 1)
            layout.addWidget(checkbox, row_index, 2)  # 添加复选框到布局
            
        return row_index + 1

    def get_model_params_settings(self):
        params = {}
        # 流式输出参数总是包含在内
        params['stream'] = self.stream_checkbox.isChecked()
        
        # 其他参数只在对应复选框选中时才添加
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
