from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QSpinBox, QHBoxLayout
from PyQt5.QtCore import Qt

class FloatingBallSettingsPage(QWidget):
    def __init__(self, floating_ball):
        super().__init__()
        self.floating_ball = floating_ball
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 透明度设置
        self.opacity_label = QLabel("透明度:", self)
        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setRange(10, 99)
        self.opacity_slider.setValue(99)  # 默认不透明
        self.opacity_spinbox = QSpinBox(self)
        self.opacity_spinbox.setRange(10, 99)
        self.opacity_spinbox.setValue(99)

        self.opacity_slider.valueChanged.connect(self.updateOpacitySpinbox)
        self.opacity_slider.valueChanged.connect(self.setBallOpacity)
        self.opacity_spinbox.valueChanged.connect(self.updateOpacitySlider)
        self.opacity_spinbox.valueChanged.connect(self.setBallOpacity)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_spinbox)

        layout.addWidget(self.opacity_label)
        layout.addLayout(opacity_layout)

        self.setLayout(layout)

    def updateOpacitySpinbox(self, value):
        self.opacity_spinbox.setValue(value)

    def updateOpacitySlider(self, value):
        self.opacity_slider.setValue(value)

    def setBallOpacity(self, opacity_value):
        opacity = opacity_value / 100.0
        self.floating_ball.setWindowOpacity(opacity)
