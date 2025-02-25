from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, 
                           QSpinBox, QHBoxLayout, QPushButton, QColorDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class FloatingBallSettingsPage(QWidget):
    def __init__(self, floating_ball):
        super().__init__()
        self.floating_ball = floating_ball
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 透明度设置
        opacity_group = self._create_setting_group("透明度:", 10, 99, 99)
        self.opacity_slider = opacity_group.slider
        self.opacity_spinbox = opacity_group.spinbox
        
        self.opacity_slider.valueChanged.connect(self.updateOpacitySpinbox)
        self.opacity_slider.valueChanged.connect(self.setBallOpacity)
        self.opacity_spinbox.valueChanged.connect(self.updateOpacitySlider)
        self.opacity_spinbox.valueChanged.connect(self.setBallOpacity)
        main_layout.addLayout(opacity_group)

        # 大小设置
        size_group = self._create_setting_group("大小:", 30, 100, 60)
        self.size_slider = size_group.slider
        self.size_spinbox = size_group.spinbox
        
        self.size_slider.valueChanged.connect(self.updateSizeSpinbox)
        self.size_slider.valueChanged.connect(self.setBallSize)
        self.size_spinbox.valueChanged.connect(self.updateSizeSlider)
        self.size_spinbox.valueChanged.connect(self.setBallSize)
        main_layout.addLayout(size_group)

        # 颜色设置
        color_group = QHBoxLayout()
        color_group.setSpacing(10)
        
        color_label = QLabel("颜色:", self)
        color_label.setMinimumWidth(60)
        
        self.color_button = QPushButton(self)
        self.color_button.setFixedSize(50, 25)
        self.current_color = QColor(180, 200, 220)  # 默认颜色
        self.update_color_button()
        self.color_button.clicked.connect(self.showColorDialog)
        
        color_group.addWidget(color_label)
        color_group.addWidget(self.color_button)
        color_group.addStretch()
        
        main_layout.addLayout(color_group)
        main_layout.addStretch()

        # 添加恢复默认设置按钮
        reset_button = QPushButton("恢复默认设置", self)
        reset_button.clicked.connect(self.resetToDefaults)
        reset_button.setFixedWidth(120)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def _create_setting_group(self, label_text, min_val, max_val, default_val):
        group = QHBoxLayout()
        group.setSpacing(10)
        
        label = QLabel(label_text, self)
        label.setMinimumWidth(60)
        
        slider = QSlider(Qt.Horizontal, self)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setFixedWidth(200)
        
        spinbox = QSpinBox(self)
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        spinbox.setFixedWidth(50)
        
        group.addWidget(label)
        group.addWidget(slider)
        group.addWidget(spinbox)
        group.addStretch()
        
        group.slider = slider
        group.spinbox = spinbox
        return group

    def update_color_button(self):
        self.color_button.setStyleSheet(
            f"background-color: {self.current_color.name()}; border: 1px solid gray;"
        )

    def showColorDialog(self):
        color = QColorDialog.getColor(self.current_color, self, "选择颜色")
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            self.setBallColor(color)

    def updateSizeSpinbox(self, value):
        self.size_spinbox.setValue(value)

    def updateSizeSlider(self, value):
        self.size_slider.setValue(value)

    def setBallSize(self, size):
        self.floating_ball.setFixedSize(size, size)

    def setBallColor(self, color):
        self.floating_ball.setColor(color)

    def updateOpacitySpinbox(self, value):
        self.opacity_spinbox.setValue(value)

    def updateOpacitySlider(self, value):
        self.opacity_slider.setValue(value)

    def setBallOpacity(self, opacity_value):
        opacity = opacity_value / 100.0
        self.floating_ball.setWindowOpacity(opacity)

    def resetToDefaults(self):
        """恢复默认设置并更新UI显示"""
        self.floating_ball.resetToDefaults()
        self.updateSettingsDisplay()

    def updateSettingsDisplay(self):
        """更新设置页面的显示"""
        self.opacity_slider.setValue(int(self.floating_ball.windowOpacity() * 100))
        self.size_slider.setValue(self.floating_ball.width())
        self.current_color = self.floating_ball.ball_color
        self.update_color_button()
