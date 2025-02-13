import sys
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient
from PyQt5.QtCore import Qt, QPoint, QRectF, QLineF, QPointF
import math

from setting_window import SettingWindow #  !!!  保留 setting_window 的导入 !!!


class FloatingBall(QWidget):

    DRAG_THRESHOLD = 10

    def __init__(self, chat_window): #  !!!  构造函数添加 chat_window 参数  !!!
        super().__init__()
        self.chat_window = chat_window #  !!!  保存 ChatWindow 实例 !!!
        self.initUI()
        self.drag_start_position = None
        self.dragging = False

    def initUI(self):
        self.setWindowTitle('透明玻璃珠悬浮球')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 60, 60)

        # 样式表 (保持之前的样式表定义)
        self.setStyleSheet("""
            FloatingBall {
                background: transparent;
            }
            QPushButton {
                background-color: rgba(220, 230, 240, 200);
                border: 1px solid rgba(100, 100, 100, 50);
                border-radius: 5px;
                padding: 5px 10px;
                color: #333;
            }
            QPushButton:hover {
                background-color: rgba(200, 210, 220, 220);
            }
            QMenu {
                background-color: rgba(240, 240, 240, 230);
                border: 1px solid rgba(100, 100, 100, 100);
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item:selected {
                background-color: rgba(180, 200, 220, 200);
            }
            QDialog {
                background-color: rgba(230, 230, 230, 240);
                border: 1px solid rgba(120, 120, 120, 150);
                border-radius: 5px;
            }
            QLabel {
                color: #333;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 5px;
                border-radius: 2px;
            }

            QSlider::sub-page:horizontal {
                background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                    stop: 0 #00aaff, stop: 1 #0055ff);
                border: 1px solid #777;
                height: 10px;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #eee;
                border: 1px solid #777;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
             QSpinBox {
                 background-color: rgba(240, 240, 240, 230);
                 border: 1px solid rgba(100, 100, 100, 100);
                 border-radius: 3px;
                 padding: 2px;
             }
        """)

        # self.paint_glass_effect()  #  !!!  修正： 注释掉 initUI 中的 paint_glass_effect() 调用 !!!


    def paint_glass_effect(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 玻璃主体渐变
        glass_gradient = QRadialGradient(self.rect().center(), self.rect().width() / 2)
        glass_gradient.setColorAt(0, QColor(240, 245, 250, 200))
        glass_gradient.setColorAt(0.7, QColor(180, 200, 220, 150))
        glass_gradient.setColorAt(1, QColor(100, 120, 140, 100))

        glass_brush = QBrush(glass_gradient)
        painter.setBrush(glass_brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())

        # 高光反射
        highlight_gradient = QRadialGradient(self.rect().topLeft() + QPoint(20, 20), 15)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 220))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))

        highlight_brush = QBrush(highlight_gradient)
        painter.setBrush(highlight_brush)
        painter.drawEllipse(QRectF(10, 10, 30, 30))

    def paintEvent(self, event):
        self.paint_glass_effect() #  !!!  paint_glass_effect() 仍然在 paintEvent 中调用，这是正确的 !!!


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.dragging = False
            print("左键按下 - 准备拖拽或点击")
        elif event.button() == Qt.RightButton:
            self.contextMenuEvent(event) #  !!!  右键仍然弹出 Context Menu  !!!

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.drag_start_position:
                distance = math.sqrt((event.pos().x() - self.drag_start_position.x())**2 + (event.pos().y() - self.drag_start_position.y())**2)
                if distance > FloatingBall.DRAG_THRESHOLD:
                    self.dragging = True
                    self.move(self.mapToGlobal(event.pos() - self.drag_start_position))
                    print("移动距离超过阈值，进入拖拽状态")


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.dragging:
                print("左键释放 - 打开/显示聊天窗口 (点击)")
                self.toggleChatWindow() #  !!!  左键点击打开/显示聊天窗口  !!!
            else:
                print("左键释放 - 结束拖拽")
            self.dragging = False
            self.drag_start_position = None


    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        setting_action = QAction("设置", self)
        setting_action.triggered.connect(self.openSettingWindow)
        context_menu.addAction(setting_action)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        context_menu.addAction(exit_action)

        context_menu.exec_(event.globalPos())

    def openSettingWindow(self):
        setting_dialog = SettingWindow(self)

        # 获取悬浮球当前在屏幕上的位置 (全局坐标)
        ball_pos = self.mapToGlobal(QPoint(0, 0)) # 获取悬浮球左上角在屏幕上的坐标

        # 计算设置窗口的理想位置 (例如，显示在悬浮球下方，稍微偏移一点)
        settings_window_x = ball_pos.x() + 20  #  水平方向向右偏移 20 像素
        settings_window_y = ball_pos.y() + self.height() + 20 # 垂直方向向下偏移 悬浮球高度 + 20 像素

        #  !!! 设置设置窗口的位置 !!!
        setting_dialog.move(settings_window_x, settings_window_y) # 移动设置窗口到计算出的位置

        setting_dialog.exec_()

    def toggleChatWindow(self): #  !!!  切换聊天窗口显示/隐藏状态的方法  !!!
            if self.chat_window.isVisible():
                self.chat_window.hide()
            else:
                # 获取悬浮球当前在屏幕上的位置 (全局坐标)
                ball_pos = self.mapToGlobal(QPoint(0, 0)) # 获取悬浮球左上角在屏幕上的坐标

                # 计算聊天窗口的理想位置 (例如，显示在悬浮球上方，稍微偏移一点)
                chat_window_x = ball_pos.x() - 350  # 水平方向向左偏移 500 像素
                chat_window_y = ball_pos.y() - self.chat_window.height() - 40 # 垂直方向向上偏移 聊天窗口高度 + 20 像素 (显示在上方)

                #  !!! 设置聊天窗口的位置 !!!
                self.chat_window.move(chat_window_x, chat_window_y) # 移动聊天窗口到计算出的位置

                self.chat_window.show()
                self.chat_window.activateWindow() #  激活窗口 (置顶)