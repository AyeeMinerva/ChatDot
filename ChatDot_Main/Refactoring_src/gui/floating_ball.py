import sys, math
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QRadialGradient
from PyQt5.QtCore import Qt, QPoint, QRectF

from gui.setting_window import SettingWindow
from gui.chat_window import ChatWindow
from core.global_managers.service_manager import ServiceManager  # 导入服务管理器

class FloatingBall(QWidget):
    DRAG_THRESHOLD = 10

    def __init__(self):
        super().__init__()
        # 添加默认值常量
        self.DEFAULT_COLOR = QColor(180, 200, 220)  # 蓝色基调
        self.DEFAULT_SIZE = 60
        self.DEFAULT_OPACITY = 0.99
        
        self.ball_color = self.DEFAULT_COLOR
        self.service_manager = ServiceManager()  # 获取服务管理器实例
        self.chat_window = ChatWindow(self)  # 保存 ChatWindow 实例
        self.setting_window = None
        self.initUI()
        self.drag_start_position = None
        self.dragging = False

    def setColor(self, color):
        self.ball_color = color
        self.update()  # 重绘悬浮球

    def initUI(self):
        self.setWindowTitle('透明玻璃珠悬浮球')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 60, 60)
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
        # 注：initUI 中不直接调用 paint_glass_effect()

    def paint_glass_effect(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        center = self.rect().center()
        
        # 主渐变
        glass_gradient = QRadialGradient(center, width / 2)
        base_color = self.ball_color
        
        # 更新渐变颜色定义
        glass_gradient.setColorAt(0, QColor(
            min(base_color.red() + 70, 255),
            min(base_color.green() + 70, 255),
            min(base_color.blue() + 70, 255),
            200
        ))
        glass_gradient.setColorAt(0.7, QColor(
            base_color.red(),
            base_color.green(),
            base_color.blue(),
            180
        ))
        glass_gradient.setColorAt(1, QColor(
            max(base_color.red() - 50, 0),
            max(base_color.green() - 50, 0),
            max(base_color.blue() - 50, 0),
            150
        ))
        
        # 绘制主体
        painter.setBrush(QBrush(glass_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())

        # 高光渐变
        highlight_size = width * 0.25
        highlight_pos = QPoint(int(width * 0.33), int(width * 0.33))
        highlight_gradient = QRadialGradient(highlight_pos, highlight_size)
        
        # 高光颜色使用更亮的主色调
        highlight_color = QColor(
            min(base_color.red() + 120, 255),
            min(base_color.green() + 120, 255),
            min(base_color.blue() + 120, 255),
            150
        )
        
        highlight_gradient.setColorAt(0, highlight_color)
        highlight_gradient.setColorAt(0.5, QColor(
            min(base_color.red() + 70, 255),
            min(base_color.green() + 70, 255),
            min(base_color.blue() + 70, 255),
            50
        ))
        highlight_gradient.setColorAt(1, QColor(
            base_color.red(),
            base_color.green(),
            base_color.blue(),
            0
        ))
        
        painter.setBrush(QBrush(highlight_gradient))
        highlight_rect = QRectF(
            width * 0.17,
            width * 0.17,
            width * 0.5,
            width * 0.5
        )
        painter.drawEllipse(highlight_rect)

    def paintEvent(self, event):
        self.paint_glass_effect()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.dragging = False
            #print("左键按下 - 准备拖拽或点击")
        elif event.button() == Qt.RightButton:
            self.contextMenuEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_start_position:
            distance = math.hypot(event.pos().x() - self.drag_start_position.x(), 
                                event.pos().y() - self.drag_start_position.y())
            if distance > FloatingBall.DRAG_THRESHOLD:
                self.dragging = True
                new_pos = self.mapToGlobal(event.pos() - self.drag_start_position)
                self.move(new_pos)
                
                # 更新聊天窗口位置
                if self.chat_window and self.chat_window.isVisible():
                    chat_pos = self.mapToGlobal(QPoint(0, 0))
                    chat_x = chat_pos.x() - 350
                    chat_y = chat_pos.y() - self.chat_window.height() - 40
                    self.chat_window.move(chat_x, chat_y)
                
                # 更新设置窗口位置
                if self.setting_window and self.setting_window.isVisible():
                    ball_pos = self.mapToGlobal(QPoint(0, 0))
                    settings_x = ball_pos.x() + 20
                    settings_y = ball_pos.y() + self.height() + 20
                    self.setting_window.move(settings_x, settings_y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.dragging:
                #print("左键释放 - 打开/显示聊天窗口 (点击)")
                self.toggleChatWindow()
            else:
                #print("左键释放 - 结束拖拽")
                pass
            self.dragging = False
            self.drag_start_position = None

    def contextMenuEvent(self, event):
        # 如果设置窗口已打开，直接关闭它而不显示右键菜单
        if self.setting_window and self.setting_window.isVisible():
            self.setting_window.close()
            return
            
        context_menu = QMenu(self)
        
        if self.chat_window.llm_thread and self.chat_window.llm_thread.isRunning():
            stop_action = QAction("停止生成", self)
            stop_action.triggered.connect(self.chat_window.stop_llm)
            context_menu.addAction(stop_action)
        
        clear_action = QAction("清除上下文", self)
        clear_action.triggered.connect(self.clear_context)  # 调用新的 clear_context 方法
        context_menu.addAction(clear_action)
        context_menu.addSeparator()
        setting_action = QAction("设置", self)
        setting_action.triggered.connect(self.openSettingWindow)
        context_menu.addAction(setting_action)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        context_menu.addAction(exit_action)
        context_menu.exec_(event.globalPos())

    def openSettingWindow(self):
        setting_window = SettingWindow(self)
        # 设置为非模态窗口
        setting_window.setWindowModality(Qt.NonModal)
        ball_pos = self.mapToGlobal(QPoint(0, 0))
        settings_window_x = ball_pos.x() + 20
        settings_window_y = ball_pos.y() + self.height() + 20
        setting_window.move(settings_window_x, settings_window_y)
        self.setting_window = setting_window
        setting_window.show()
        
    def closeSettingWindow(self):
        if self.setting_window and self.setting_window.isVisible():
            self.setting_window.close()

    def toggleChatWindow(self):
        if self.chat_window.isVisible():
            self.chat_window.hide()
        else:
            ball_pos = self.mapToGlobal(QPoint(0, 0))
            chat_x = ball_pos.x() - 350
            chat_y = ball_pos.y() - self.chat_window.height() - 40
            self.chat_window.move(chat_x, chat_y)
            self.chat_window.show()
            self.chat_window.activateWindow()

    def resetToDefaults(self):
        """恢复默认设置"""
        self.setFixedSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE)
        self.setColor(self.DEFAULT_COLOR)
        self.setWindowOpacity(self.DEFAULT_OPACITY)
        # 通知设置页面更新显示
        if hasattr(self, 'setting_window'):
            self.setting_window.floating_ball_settings_page.updateSettingsDisplay()

    def clear_context(self):
        """调用核心服务清除上下文"""
        chat_service = self.service_manager.get_service("chat_service")
        chat_service.clear_context()
        self.chat_window.clear_chat_display()  # 清除聊天窗口显示