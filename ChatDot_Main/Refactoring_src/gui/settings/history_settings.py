from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal

class HistorySettingsPage(QWidget):
    load_history_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Load History Button
        load_button = QPushButton("加载历史记录")
        load_button.clicked.connect(self.load_history)
        main_layout.addWidget(load_button)

        self.setLayout(main_layout)

    def load_history(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "加载历史记录", "", "JSON Files (*.json)")
        if file_path:
            self.load_history_requested.emit(file_path)