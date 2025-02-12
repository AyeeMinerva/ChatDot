from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient
from PyQt5.QtCore import Qt, QPoint, QRectF

class FloatingBall(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.drag_position = None

    def initUI(self):
        self.setWindowTitle('透明玻璃珠悬浮球')  # 窗口标题 -  可以在这里设置，也可以在 main.py 中设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 60, 60)  # 初始位置和大小

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 玻璃主体渐变 -  浅蓝色玻璃色调 (样式参数可以考虑提取到单独的类或配置中)
        glass_gradient = QRadialGradient(self.rect().center(), self.rect().width() / 2)
        glass_gradient.setColorAt(0, QColor(240, 245, 250, 200))
        glass_gradient.setColorAt(0.7, QColor(180, 200, 220, 150))
        glass_gradient.setColorAt(1, QColor(100, 120, 140, 100))

        glass_brush = QBrush(glass_gradient)
        painter.setBrush(glass_brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())

        # 高光反射 -  更小更亮的白色高光 (样式参数可以考虑提取)
        highlight_gradient = QRadialGradient(self.rect().topLeft() + QPoint(20, 20), 15)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 220))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))

        highlight_brush = QBrush(highlight_gradient)
        painter.setBrush(highlight_brush)
        painter.drawEllipse(QRectF(10, 10, 30, 30))

        # (可选) 内阴影 - 可以尝试添加，如果效果不佳可以移除

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
        exit_action.triggered.connect(QApplication.instance().quit)  # 退出程序 -  保持在 FloatingBall 类中，方便右键菜单操作
        context_menu.addAction(exit_action)
        context_menu.exec_(event.globalPos())