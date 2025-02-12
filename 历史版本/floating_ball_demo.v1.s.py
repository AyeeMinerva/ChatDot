import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QConicalGradient, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QRectF

class FloatingBall(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.drag_position = None

    def initUI(self):
        self.setWindowTitle('透明玻璃珠悬浮球') # 窗口标题
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setGeometry(100, 100, 60, 60)

        # 移除外阴影效果 -  对于玻璃珠子，外阴影可能不合适
        # shadow_effect = QGraphicsDropShadowEffect()
        # self.setGraphicsEffect(shadow_effect)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 玻璃主体渐变 -  浅蓝色玻璃色调
        glass_gradient = QRadialGradient(self.rect().center(), self.rect().width() / 2)
        glass_gradient.setColorAt(0, QColor(240, 245, 250, 200)) # 中心颜色，非常浅的蓝色，略微透明
        glass_gradient.setColorAt(0.7, QColor(180, 200, 220, 150)) # 中间颜色，浅蓝色，更透明
        glass_gradient.setColorAt(1, QColor(100, 120, 140, 100)) # 边缘颜色，深蓝色，更透明

        glass_brush = QBrush(glass_gradient)
        painter.setBrush(glass_brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())


        # 高光反射 -  更小更亮的白色高光，移到左上角
        highlight_gradient = QRadialGradient(self.rect().topLeft() + QPoint(20, 20), 15) #  中心更靠近左上角，半径更小
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 220)) #  更亮的白色，略微透明
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))   #  边缘透明

        highlight_brush = QBrush(highlight_gradient)
        painter.setBrush(highlight_brush)
        painter.drawEllipse(QRectF(10, 10, 30, 30)) # 绘制一个更小的圆形作为高光，位置和大小需要调整


        # (可选) 内阴影 -  可以尝试添加，如果效果不佳可以移除


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            print("左键点击悬浮球！")
        elif event.button() == Qt.RightButton:
            self.contextMenuEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.drag_position:
                self.move(event.globalPos() - self.drag_position)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        context_menu.addAction(exit_action)
        context_menu.exec_(event.globalPos())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    fb = FloatingBall()
    fb.show()
    sys.exit(app.exec_())