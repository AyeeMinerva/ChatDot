from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFormLayout

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)

        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_base_input = QLineEdit()
        self.model_name_input = QLineEdit()
        self.model_params_input = QLineEdit()

        self.form_layout.addRow(QLabel("API Key:"), self.api_key_input)
        self.form_layout.addRow(QLabel("API Base URL:"), self.api_base_input)
        self.form_layout.addRow(QLabel("Default Model:"), self.model_name_input)
        self.form_layout.addRow(QLabel("Model Parameters:"), self.model_params_input)

        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def save_settings(self):
        api_key = self.api_key_input.text()
        api_base = self.api_base_input.text()
        model_name = self.model_name_input.text()
        model_params = self.model_params_input.text()

        # Here you would typically save these settings to a config file or service
        print(f"Settings saved: API Key: {api_key}, API Base: {api_base}, Model: {model_name}, Params: {model_params}")
        self.accept()  # Close the dialog after saving

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.exec_()