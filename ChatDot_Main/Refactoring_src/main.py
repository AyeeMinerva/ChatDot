from PyQt5.QtWidgets import QApplication
import sys
from gui.main_window import MainWindow
from core.bootstrap import Bootstrap

def main():
    app = QApplication(sys.argv)
    bootstrap = Bootstrap()
    bootstrap.initialize()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()