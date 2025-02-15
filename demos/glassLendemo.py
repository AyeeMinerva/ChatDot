#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

class LensWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # 设置无边框、置顶和工具窗口（避免出现在任务栏中）
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint |
                            QtCore.Qt.Tool)
        # 背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # 禁止系统自动清除背景（减少闪烁）
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.resize(300, 300)
        # 限制绘制区域为圆形
        self.setMask(QtGui.QRegion(self.rect(), QtGui.QRegion.Ellipse))

        # 拖动起始位置
        self.drag_position = None

        # 缓存截屏和经过透镜扭曲后的图像
        self.bg_cache = None
        self.distorted_cache = None

        # 标记是否正在更新中，避免重入
        self.updating = False

        # 定时器：动态刷新背景（例如每 100 毫秒一次，可根据需要调整）
        self.bg_timer = QtCore.QTimer(self)
        self.bg_timer.timeout.connect(self.updateBackground)
        self.bg_timer.start(100)

    def updateBackground(self):
        """更新当前窗口所在区域的桌面背景，并计算透镜扭曲效果。"""
        if self.updating:
            return
        self.updating = True

        pos = self.mapToGlobal(QtCore.QPoint(0, 0))
        screen = QtWidgets.QApplication.primaryScreen()

        # 为减少闪烁，先关闭窗口更新，并临时调低窗口不透明度
        self.setUpdatesEnabled(False)
        old_opacity = self.windowOpacity()
        self.setWindowOpacity(0)
        # 让界面立即刷新（但不响应用户输入）
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)

        # 截取窗口所在区域的桌面图像
        screenshot = screen.grabWindow(0, pos.x(), pos.y(), self.width(), self.height())
        self.bg_cache = screenshot.toImage().convertToFormat(QtGui.QImage.Format_ARGB32)

        # 恢复不透明度与更新
        self.setWindowOpacity(old_opacity)
        self.setUpdatesEnabled(True)

        # 根据截屏生成透镜扭曲后的图像
        self.createDistortedImage()
        self.update()  # 通知重绘

        self.updating = False

    def createDistortedImage(self):
        """对缓存的背景图像进行透镜扭曲处理，结果保存到 self.distorted_cache"""
        if self.bg_cache is None:
            return

        qimage = self.bg_cache
        w = qimage.width()
        h = qimage.height()

        # 将 QImage 转换为 numpy 数组
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        img_arr = np.array(ptr).reshape(h, w, 4).copy()

        # 输出图像数组（浮点数便于计算）
        out_arr = np.zeros_like(img_arr, dtype=np.float32)

        # 透镜参数：以窗口中心为光轴，半径为窗口短边一半，中心放大1.5倍
        center_x = w / 2.0
        center_y = h / 2.0
        radius = min(w, h) / 2.0
        magnification = 1.5

        # 构造二维坐标网格
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)

        dx = X - center_x
        dy = Y - center_y
        r = np.sqrt(dx**2 + dy**2)

        # 非线性放大因子：中心处 f = magnification，边缘 f = 1
        f = np.ones_like(r)
        mask = r <= radius
        f[mask] = (magnification - 1) * (1 - (r[mask] / radius) ** 2) + 1

        # 反向映射：目标像素 (X, Y) 对应源图像坐标 (src_X, src_Y)
        src_X = center_x + dx / f
        src_Y = center_y + dy / f

        # 双线性插值：先确定周围的整数像素
        src_X0 = np.floor(src_X).astype(np.int32)
        src_Y0 = np.floor(src_Y).astype(np.int32)
        src_X1 = np.clip(src_X0 + 1, 0, w - 1)
        src_Y1 = np.clip(src_Y0 + 1, 0, h - 1)
        wx = src_X - src_X0
        wy = src_Y - src_Y0

        src_X0 = np.clip(src_X0, 0, w - 1)
        src_Y0 = np.clip(src_Y0, 0, h - 1)

        # 取出四个邻域像素值
        I00 = img_arr[src_Y0, src_X0].astype(np.float32)
        I10 = img_arr[src_Y0, src_X1].astype(np.float32)
        I01 = img_arr[src_Y1, src_X0].astype(np.float32)
        I11 = img_arr[src_Y1, src_X1].astype(np.float32)

        # 计算双线性插值权重
        w0 = (1 - wx) * (1 - wy)
        w1 = wx * (1 - wy)
        w2 = (1 - wx) * wy
        w3 = wx * wy

        out_arr = (I00 * w0[..., None] +
                   I10 * w1[..., None] +
                   I01 * w2[..., None] +
                   I11 * w3[..., None])

        # 对圆形区域外的像素设为全透明（alpha = 0）
        out_arr[r > radius, 3] = 0

        out_arr = np.clip(out_arr, 0, 255).astype(np.uint8)

        # 构造 QImage（调用 .copy() 以确保数据独立）
        self.distorted_cache = QtGui.QImage(out_arr.data, w, h, out_arr.strides[0],
                                             QtGui.QImage.Format_ARGB32).copy()

    def paintEvent(self, event):
        """只绘制缓存的透镜图像"""
        painter = QtGui.QPainter(self)
        if self.distorted_cache:
            painter.drawImage(0, 0, self.distorted_cache)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # 记录鼠标相对于窗口左上角的偏移量
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            # 拖动移动窗口，定时器会自动刷新背景
            self.move(event.globalPos() - self.drag_position)
            event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    lens = LensWindow()
    lens.show()
    sys.exit(app.exec_())
