# -*- coding: utf-8 -*-
"""排轴窗口使用的独立 Qt 小控件。"""

from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QWidget, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QPainter

class _StatePanel(QFrame):
    """「状态总览」容器：标题单独占一行。

    不用 QGroupBox 的标题：它的标题画在边框上，某些字体 / 缩放下
    预留高度不足，会被下面的表格表头压掉下半截。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statePanel")
        self.setFrameShape(QFrame.StyledPanel)
        self.title_label = QLabel()
        self.title_label.setTextFormat(Qt.PlainText)
        self.title_label.setStyleSheet(
            "font-weight: bold; padding: 2px 0 2px 2px;")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(8, 4, 8, 4)
        self.body.setSpacing(4)
        self.body.addWidget(self.title_label)

    def setTitle(self, text):
        self.title_label.setText(text)

    def title(self):
        return self.title_label.text()

class _AspectCanvas(QWidget):
    """按控件宽度显示图片，高度按宽高比自动增长（超长时交给外层滚动）。"""

    def __init__(self, source=None, parent=None):
        super().__init__(parent)
        self._src = None
        self._last = None
        self._cached_pixmap = None
        self._cached_size = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(80)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._delayed_sync)
        if source is not None:
            self.set_source(source)

    # ------------------------------------------------------------ 数据
    def set_source(self, source):
        self._src = source
        self._cached_pixmap = None
        self._cached_size = None
        self._sync_height()
        self.update()

    def source(self):
        return self._src

    def drawn(self):
        """最近一次绘制用的像素图（测试用）。"""
        return self._last

    def target_height(self, width=None):
        """给定宽度下，按原图宽高比算出的显示高度（不超过原图尺寸）。"""
        if self._src is None or self._src.isNull() or self._src.width() <= 0:
            return 80
        w = self.width() if width is None else width
        if w >= self._src.width():          # 比原图窄才缩放；否则保持原尺寸
            return self._src.height()
        return int(round(w * self._src.height() / float(self._src.width())))

    def _sync_height(self):
        h = max(80, self.target_height())
        if self.minimumHeight() != h:
            self.setMinimumHeight(h)

    # ------------------------------------------------------------ Qt
    def sizeHint(self):
        if self._src is None or self._src.isNull():
            return QSize(480, 320)
        return QSize(self._src.width(), self._src.height())

    def minimumSizeHint(self):
        return QSize(160, 80)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 拖拽缩放期间只防抖同步高度/缓存，避免每次事件 Smooth 全图重缩放
        self._resize_timer.start(50)

    def _delayed_sync(self):
        self._sync_height()
        self._cached_pixmap = None
        self._cached_size = None
        self.update()

    def paintEvent(self, event):
        if self._src is None or self._src.isNull():
            return
        w = self.width()
        h = max(80, self.target_height())
        size = QSize(w, h)
        if self._cached_pixmap is None or self._cached_size != size:
            # 拖拽中用快速插值，静止后由防抖回调清缓存再用 Smooth 重画
            smooth = (not self._resize_timer.isActive())
            self._cached_size = size
            self._cached_pixmap = self._src.scaled(
                w, h, Qt.KeepAspectRatio,
                Qt.SmoothTransformation if smooth else Qt.FastTransformation)
        self._last = self._cached_pixmap
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cached_pixmap)


class _ScaledImageView(QScrollArea):
    """轴图查看器：**宽度始终铺满窗口**（超长时出现垂直滚动条，不压缩变形）。"""

    def __init__(self, pixmap=None, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)                 # 画布宽度跟随可视区
        self.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._canvas = _AspectCanvas()
        self.setWidget(self._canvas)
        if pixmap is not None:
            self.set_source(pixmap)

    def set_source(self, pixmap):
        self._canvas.set_source(pixmap)

    def source(self):
        return self._canvas.source()

    def canvas(self):
        return self._canvas
