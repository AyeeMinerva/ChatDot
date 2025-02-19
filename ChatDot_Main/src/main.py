import sys
from PyQt5.QtWidgets import QApplication
from gui.chat_window import ChatWindow
from gui.floating_ball import FloatingBall

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #chat_window = ChatWindow()
    floating_ball = FloatingBall()
    floating_ball.show()
    sys.exit(app.exec_())
