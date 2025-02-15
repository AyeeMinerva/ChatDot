import os
os.environ['PYTHONIOENCODING'] = 'UTF-8'

import sys
from PyQt5.QtWidgets import QApplication
from floating_ball import FloatingBall
from setting_window import SettingWindow
from chat_window import ChatWindow #  !!! 导入 ChatWindow !!!


if __name__ == "__main__":
    
    app = QApplication(sys.argv)

    chat_window = ChatWindow() #  !!!  先创建 ChatWindow 实例 !!!
    floating_ball = FloatingBall(chat_window)
    floating_ball.show()

    setting_dialog = SettingWindow(floating_ball)
    floating_ball.setting_dialog = setting_dialog


    setting_dialog.api_connected_signal.connect(chat_window.enable_send_buttons) #  !!!  连接 API 连接成功信号 !!!

    sys.exit(app.exec_())