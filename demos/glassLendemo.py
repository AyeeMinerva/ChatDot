#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import (
    QOpenGLShader, QOpenGLShaderProgram, QOpenGLBuffer,
    QOpenGLVertexArrayObject, QOpenGLTexture, QSurfaceFormat, QImage
)
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtOpenGL import QOpenGLFunctions


class GlassBeadWidget(QOpenGLWidget, QOpenGLFunctions):
    def __init__(self, parent=None):
        super(GlassBeadWidget, self).__init__(parent)
        self.desktop_texture = None     # 用于保存桌面截图纹理
        self.shader_program = None      # OpenGL 着色器程序
        self.vbo = None                 # 顶点缓冲区对象
        self.vao = None                 # 顶点数组对象
        self.drag_position = None       # 拖动时记录鼠标偏移

        # 定时器：每 30 毫秒更新一次桌面纹理（约 33fps）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateDesktopTexture)
        self.timer.start(30)

        # 设置窗口：无边框、始终置顶、工具窗口，并要求透明背景
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        # 限制窗口显示区域为圆形（与窗口矩形重合）
        self.setMask(QtGui.QRegion(self.rect(), QtGui.QRegion.Ellipse))

    def initializeGL(self):
        self.initializeOpenGLFunctions()
        self.glClearColor(0.0, 0.0, 0.0, 0.0)

        # --- 构建着色器程序 ---
        self.shader_program = QOpenGLShaderProgram(self)

        vertex_shader_source = """
        #version 330 core
        layout(location = 0) in vec2 position;
        layout(location = 1) in vec2 texCoord;
        out vec2 vTexCoord;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
            vTexCoord = texCoord;
        }
        """
        fragment_shader_source = """
        #version 330 core
        in vec2 vTexCoord;
        out vec4 fragColor;
        uniform sampler2D desktopTexture;
        uniform float magnification;
        void main(){
            // 用纹理坐标（0~1）计算中心偏移
            vec2 center = vec2(0.5, 0.5);
            vec2 uv = vTexCoord;
            vec2 offset = uv - center;
            float r = length(offset);
            float radius = 0.5;  // 半径（归一化）
            float factor = 1.0;
            if(r < radius){
                // 中心放大：距离越近，放大越多
                factor = (magnification - 1.0) * (1.0 - (r / radius) * (r / radius)) + 1.0;
            }
            vec2 distortedUV = center + offset / factor;
            vec4 color = texture(desktopTexture, distortedUV);

            // --- 添加玻璃珠高光效果 ---
            // 以一个预设的高光中心产生平滑高光（可根据需要调整参数）
            vec2 highlightCenter = vec2(0.35, 0.35);
            float d = distance(uv, highlightCenter);
            float highlight = smoothstep(0.4, 0.0, d); // 距离越近，高光越强
            color.rgb = mix(color.rgb, vec3(1.0), highlight * 0.3);

            fragColor = color;
        }
        """
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, vertex_shader_source)
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, fragment_shader_source)
        self.shader_program.link()

        # --- 设置用于绘制满屏四边形的顶点数据 ---
        # 顶点数据：每个顶点包含 2 个位置坐标和 2 个纹理坐标
        vertices = np.array([
            # positions    # texCoords
            -1.0, -1.0,    0.0, 0.0,
             1.0, -1.0,    1.0, 0.0,
            -1.0,  1.0,    0.0, 1.0,
             1.0,  1.0,    1.0, 1.0,
        ], dtype=np.float32)

        # --- 创建顶点数组对象（VAO） ---
        self.vao = QOpenGLVertexArrayObject(self)
        self.vao.create()
        self.vao.bind()

        # --- 创建顶点缓冲对象（VBO）并上传数据 ---
        self.vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.vbo.create()
        self.vbo.bind()
        self.vbo.allocate(vertices.tobytes(), vertices.nbytes)

        # 设置属性指针：注意 stride 为 4 个浮点数（4*4=16 字节）
        # 位置属性：起始偏移 0，2 个浮点数
        self.shader_program.enableAttributeArray(0)
        self.shader_program.setAttributeBuffer(0, self.GL_FLOAT, 0, 2, 4 * 4)
        # 纹理坐标属性：起始偏移 2*4 字节，2 个浮点数
        self.shader_program.enableAttributeArray(1)
        self.shader_program.setAttributeBuffer(1, self.GL_FLOAT, 2 * 4, 2, 4 * 4)

        self.vbo.release()
        self.vao.release()

    def updateDesktopTexture(self):
        """
        每次调用时：  
         1. 根据窗口在桌面上的位置，用 QScreen.grabWindow 获取该区域截图  
         2. 临时将窗口透明，避免截到自身内容  
         3. 将截图上传到 GPU 纹理
        """
        pos = self.mapToGlobal(QPoint(0, 0))
        screen = QtWidgets.QApplication.primaryScreen()
        # 为避免截图包含本窗口内容，先将窗口透明
        old_opacity = self.windowOpacity()
        self.setWindowOpacity(0)
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
        pixmap = screen.grabWindow(0, pos.x(), pos.y(), self.width(), self.height())
        self.setWindowOpacity(old_opacity)
        # 转换为 32 位 RGBA 格式（注意不同 Qt 版本支持的格式可能有所不同）
        image = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)

        # 上传图像到纹理（窗口尺寸较小，所以全图上传开销不大）
        if self.desktop_texture is None:
            self.desktop_texture = QOpenGLTexture(image)
            self.desktop_texture.setMinificationFilter(QOpenGLTexture.Linear)
            self.desktop_texture.setMagnificationFilter(QOpenGLTexture.Linear)
            self.desktop_texture.setWrapMode(QOpenGLTexture.ClampToEdge)
        else:
            self.desktop_texture.bind()
            self.desktop_texture.setData(image)

        self.update()  # 触发 repaint

    def paintGL(self):
        self.glClear(self.GL_COLOR_BUFFER_BIT | self.GL_DEPTH_BUFFER_BIT)
        self.shader_program.bind()
        self.vao.bind()

        if self.desktop_texture:
            self.desktop_texture.bind(0)
            self.shader_program.setUniformValue("desktopTexture", 0)
        # 设置放大倍数（可调）
        self.shader_program.setUniformValue("magnification", 1.5)

        # 绘制全屏四边形（采用三角带方式绘制 4 个顶点）
        self.glDrawArrays(self.GL_TRIANGLE_STRIP, 0, 4)

        self.vao.release()
        self.shader_program.release()

    def resizeGL(self, w, h):
        self.glViewport(0, 0, w, h)
        # 随窗口尺寸变化重新设置圆形遮罩
        self.setMask(QtGui.QRegion(self.rect(), QtGui.QRegion.Ellipse))

    # --- 实现鼠标拖动窗口 ---
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    # 指定 OpenGL 上下文版本（3.3 核心）以保证着色器能正常工作
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = GlassBeadWidget()
    window.resize(300, 300)
    window.show()
    sys.exit(app.exec_())
