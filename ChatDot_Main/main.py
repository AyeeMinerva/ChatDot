import sys
from PyQt5.QtWidgets import QApplication
from floating_ball import FloatingBall  # 导入 FloatingBall 类

def main():
    app = QApplication(sys.argv)
    fb = FloatingBall() # 创建 FloatingBall 实例
    fb.setWindowTitle('透明玻璃珠悬浮球') # 窗口标题 -  也可以在这里设置
    fb.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()