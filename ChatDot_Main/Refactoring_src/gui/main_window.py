from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from chat_window import ChatWindow
from settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatDot Application")
        self.setGeometry(100, 100, 800, 600)

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        chat_action = QAction("Chat", self)
        chat_action.triggered.connect(self.open_chat_window)
        file_menu.addAction(chat_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Help")
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def open_chat_window(self):
        self.chat_window = ChatWindow()
        self.chat_window.show()

    def open_settings_dialog(self):
        self.settings_dialog = SettingsDialog()
        self.settings_dialog.exec_()

    def show_help(self):
        QMessageBox.information(self, "Help", "This is the help dialog.")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())