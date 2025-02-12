import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QGraphicsBlurEffect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QConicalGradient, QLinearGradient, QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect

class FloatingBall(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.drag_position = None

    def initUI(self):
        self.setWindowTitle('毛玻璃背景悬浮球') # 窗口标题
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 60, 60) # 保持尺寸

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 捕获屏幕区域
        screen = QApplication.primaryScreen()
        screen_pixmap = screen.grabWindow(self) # 捕获悬浮球窗口下的屏幕区域
        screen_image = screen_pixmap.toImage()

        # 2. 创建模糊效果
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(15) # 设置模糊半径，可以调整
        blurred_pixmap = screen_pixmap.transformed(blur_effect.blurTransformation(QRectF(screen_pixmap.rect())))
        blurred_image = blurred_pixmap.toImage()


        # 3. 绘制模糊后的背景
        painter.drawImage(self.rect(), blurred_image)


        # 4. 绘制玻璃主体 (与之前的透明玻璃珠版本相同)
        glass_gradient = QRadialGradient(self.rect().center(), self.rect().width() / 2)
        glass_gradient.setColorAt(0, QColor(240, 245, 250, 200)) # 中心颜色
        glass_gradient.setColorAt(0.7, QColor(180, 200, 220, 150)) # 中间颜色
        glass_gradient.setColorAt(1, QColor(100, 120, 140, 100)) # 边缘颜色

        glass_brush = QBrush(glass_gradient)
        painter.setBrush(glass_brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())

        # 5. 绘制高光 (与之前的透明玻璃珠版本相同)
        highlight_gradient = QRadialGradient(self.rect().topLeft() + QPoint(20, 20), 15)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 220)) # 更亮的白色，略微透明
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))   # 边缘透明

        highlight_brush = QBrush(highlight_gradient)
        painter.setBrush(highlight_brush)
        painter.drawEllipse(QRectF(10, 10, 30, 30))


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