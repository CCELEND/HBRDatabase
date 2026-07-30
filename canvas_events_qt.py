import os
import cv2
import numpy as np
import threading
import queue
import time

from PIL import Image

from PyQt5.QtWidgets import (
    QLabel, QWidget, QScrollArea, QVBoxLayout, QGridLayout,
    QSizePolicy, QMainWindow
)
from PyQt5.QtCore import Qt, QObject, QTimer, QSize, QRect, pyqtSignal, QEvent
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QCursor
)


pixmap_cache = {}
# def get_pixmap(img_path: str, img_resize: tuple) -> QPixmap:
#     unique_key = f"{img_path}_{img_resize}"
#     if unique_key in pixmap_cache:
#         return pixmap_cache[unique_key]

#     if not os.path.exists(img_path):
#         return QPixmap()

#     try:
#         np_arr = np.fromfile(img_path, dtype=np.uint8)
#         img_array = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

#         if img_array is None:
#             raise Exception("OpenCV decode failed")

#         # img_resized = cv2.resize(img_array, img_resize, interpolation=cv2.INTER_LANCZOS4)
#         # img_resized = cv2.resize(img_array, img_resize, interpolation=cv2.INTER_CUBIC)
#         # img_resized = cv2.resize(img_array, img_resize, interpolation=cv2.INTER_LINEAR) 
#         img_resized = cv2.resize(img_array, img_resize, interpolation=cv2.INTER_AREA)
#         if img_resized.ndim == 2:
#             h, w = img_resized.shape
#             qimg = QImage(img_resized.data, w, h, w, QImage.Format_Grayscale8)
#         elif img_resized.shape[2] == 4:
#             h, w, ch = img_resized.shape
#             rgba = cv2.cvtColor(img_resized, cv2.COLOR_BGRA2RGBA)
#             qimg = QImage(rgba.data, w, h, ch * w, QImage.Format_RGBA8888)
#         else:
#             h, w, ch = img_resized.shape
#             rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
#             qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
#         pixmap = QPixmap.fromImage(qimg.copy())
#     except Exception:
#         try:
#             pil_image = Image.open(img_path)
#             pil_image = pil_image.resize(img_resize, Image.LANCZOS)
#             if pil_image.mode == 'RGBA':
#                 qimg = QImage(pil_image.tobytes("raw", "RGBA"),
#                               pil_image.width, pil_image.height,
#                               pil_image.width * 4, QImage.Format_RGBA8888)
#             else:
#                 pil_image = pil_image.convert('RGB')
#                 qimg = QImage(pil_image.tobytes("raw", "RGB"),
#                               pil_image.width, pil_image.height,
#                               pil_image.width * 3, QImage.Format_RGB888)
#             pixmap = QPixmap.fromImage(qimg.copy())
#         except Exception:
#             return QPixmap()

#     pixmap_cache[unique_key] = pixmap
#     return pixmap

def get_pixmap(img_path: str, img_resize: tuple) -> QPixmap:
    """
    加载图片并缩放为指定尺寸的 QPixmap，带缓存。
    缩小时使用 INTER_AREA 保证平滑，放大时使用 INTER_CUBIC 保证质量。
    """
    # 将插值策略纳入缓存key，避免切换算法后命中旧缓存
    unique_key = f"{img_path}_{img_resize}"
    if unique_key in pixmap_cache:
        return pixmap_cache[unique_key]

    if not os.path.exists(img_path):
        return QPixmap()

    try:
        np_arr = np.fromfile(img_path, dtype=np.uint8)
        img_array = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

        if img_array is None:
            raise Exception("OpenCV decode failed")

        # ---------- 动态选择插值方式 ----------
        h_orig, w_orig = img_array.shape[:2]
        is_downscale = img_resize[0] < w_orig or img_resize[1] < h_orig

        if is_downscale:
            # 缩小：INTER_AREA 基于区域重采样，最平滑无锯齿
            interpolation = cv2.INTER_AREA
        else:
            # 放大：INTER_CUBIC 比 INTER_LINEAR 更细腻
            interpolation = cv2.INTER_CUBIC

        img_resized = cv2.resize(img_array, img_resize, interpolation=interpolation)

        # ---------- 可选：对极小图做轻微抗锯齿平滑 ----------
        if is_downscale and max(img_resize) <= 128:
            img_resized = cv2.GaussianBlur(img_resized, (3, 3), sigmaX=0.35)

        # ---------- 转换为 QImage ----------
        if img_resized.ndim == 2:
            h, w = img_resized.shape
            qimg = QImage(img_resized.data, w, h, w, QImage.Format_Grayscale8)
        elif img_resized.shape[2] == 4:
            h, w, ch = img_resized.shape
            rgba = cv2.cvtColor(img_resized, cv2.COLOR_BGRA2RGBA)
            qimg = QImage(rgba.data, w, h, ch * w, QImage.Format_RGBA8888)
        else:
            h, w, ch = img_resized.shape
            rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)

        # copy() 是必须的：OpenCV 数组内存会被回收，不 copy 会导致花屏/崩溃
        pixmap = QPixmap.fromImage(qimg.copy())

    except Exception:
        # ---------- PIL Fallback ----------
        try:
            pil_image = Image.open(img_path)
            # PIL LANCZOS 在缩小和放大场景下质量都很好
            pil_image = pil_image.resize(img_resize, Image.Resampling.LANCZOS)

            if pil_image.mode == 'RGBA':
                qimg = QImage(
                    pil_image.tobytes("raw", "RGBA"),
                    pil_image.width, pil_image.height,
                    pil_image.width * 4, QImage.Format_RGBA8888
                )
            else:
                pil_image = pil_image.convert('RGB')
                qimg = QImage(
                    pil_image.tobytes("raw", "RGB"),
                    pil_image.width, pil_image.height,
                    pil_image.width * 3, QImage.Format_RGB888
                )
            pixmap = QPixmap.fromImage(qimg.copy())
        except Exception:
            return QPixmap()

    pixmap_cache[unique_key] = pixmap
    return pixmap


class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    doubleClicked = pyqtSignal()
    rightClicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMouseTracking(True)
        self._border_visible = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit()
            self.right_clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        self._border_visible = True
        self.setStyleSheet("border: 2px solid #93CBE4;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._border_visible = False
        self.setStyleSheet("border: none;")
        super().leaveEvent(event)


def create_image_label(parent: QWidget, pixmap: QPixmap,
                       width: int, height: int,
                       row: int = 0, column: int = 0,
                       rowspan: int = 1, columnspan: int = 1,
                       padx: int = 5, pady: int = 5) -> ClickableLabel:
    label = ClickableLabel(parent)
    if not pixmap.isNull():
        label.setPixmap(pixmap)
    label.setFixedSize(width, height)
    label.setAlignment(Qt.AlignCenter)
    label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    parent_layout = parent.layout()
    if parent_layout is not None:
        from PyQt5.QtWidgets import QGridLayout
        if isinstance(parent_layout, QGridLayout):
            parent_layout.addWidget(label, row, column, rowspan, columnspan)
        else:
            parent_layout.addWidget(label)

    return label


def create_canvas_with_image(parent_frame: QWidget,
                             pixmap: QPixmap,
                             canvas_width, canvas_height,
                             row, column,
                             rowspan=1, columnspan=1,
                             padx=5, pady=5) -> ClickableLabel:
    return create_image_label(parent_frame, pixmap, canvas_width, canvas_height,
                              row, column, rowspan, columnspan, padx, pady)


class _FakeEvent:
    def __init__(self, widget=None):
        self.widget = widget
    def globalPos(self):
        return QCursor.pos()


def bind_canvas_events(label: ClickableLabel, click_handler=None, **kwargs):
    if click_handler:
        label.clicked.connect(lambda: click_handler(_FakeEvent(label), **kwargs))


def double_click_bind_canvas_events(label: ClickableLabel, double_click_handler=None, **kwargs):
    if double_click_handler:
        label.doubleClicked.connect(
            lambda: double_click_handler(_FakeEvent(label), **kwargs))


def right_click_bind_canvas_events(label: ClickableLabel, right_click_handler=None, **kwargs):
    if right_click_handler:
        label.rightClicked.connect(
            lambda: right_click_handler(_FakeEvent(label), **kwargs))


def mouse_bind_canvas_events(label: ClickableLabel):
    label.setCursor(QCursor(Qt.PointingHandCursor))


def mouse_bind_canvas_events2(label: ClickableLabel):
    label.setCursor(QCursor(Qt.PointingHandCursor))


def set_tooltip(widget: QWidget, text: str):
    widget.setToolTip(text)
    widget.setToolTipDuration(5000)


def _get_layout_target(widget):
    if isinstance(widget, QMainWindow):
        central = widget.centralWidget()
        if central is None:
            central = QWidget(widget)
            widget.setCentralWidget(central)
        return central
    return widget


class ArtworkDisplayerHeight:
    def __init__(self, parent_widget: QWidget, artwork_path: str,
                 target_height: int, padding: int = 0, opacity: str = "100%"):
        self.padding = padding
        self.parent_widget = parent_widget
        self.artwork_path = artwork_path
        self.target_height = target_height

        opacity_percentage = int(opacity.strip('%')) / 100
        self.gray_value = int(opacity_percentage * 255)

        self.load_and_resize_image()

        canvas_width = self.target_width + 2 * self.padding

        self.label = QLabel(parent_widget)
        self.label.setPixmap(self._pixmap)
        self.label.setFixedSize(canvas_width, self.target_height)
        self.label.setAlignment(Qt.AlignCenter)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            parent_layout.addWidget(self.label)

    def load_and_resize_image(self):
        self.original_image = Image.open(self.artwork_path)
        original_width, original_height = self.original_image.size
        self.target_width = int(original_width * (self.target_height / original_height))

        self.resized_image = self.original_image.resize(
            (self.target_width, self.target_height), Image.LANCZOS
        )

        if self.gray_value != 255:
            mask = Image.new('L', self.resized_image.size, self.gray_value)
            self.resized_image.putalpha(mask)

        if self.resized_image.mode == 'RGBA':
            qimg = QImage(self.resized_image.tobytes("raw", "RGBA"),
                          self.resized_image.width, self.resized_image.height,
                          self.resized_image.width * 4, QImage.Format_RGBA8888)
        else:
            self.resized_image = self.resized_image.convert('RGB')
            qimg = QImage(self.resized_image.tobytes("raw", "RGB"),
                          self.resized_image.width, self.resized_image.height,
                          self.resized_image.width * 3, QImage.Format_RGB888)

        self._pixmap = QPixmap.fromImage(qimg.copy())

    def destroy(self):
        self.label.deleteLater()
        self._pixmap = None
        self.original_image.close()

class _ResizableArtworkLabel(QLabel):
    def __init__(self, parent_widget, artwork_path, opacity_value):
        super().__init__(parent_widget)
        self.opacity_value = opacity_value
        self.original_image = Image.open(artwork_path)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._cached_size = None
        self._cached_pixmap = None
        self._updating_height = False

        # ---- 新增防抖定时器 ----
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._delayed_update)
        self._pending_width = None

        # 初始化时计算一次高度
        self._update_height()

    def _target_height(self, width=None):
        if width is None:
            width = self.width()
        if width <= 0:
            return 1
        orig_w, orig_h = self.original_image.size
        return max(1, int(width * orig_h / orig_w))

    def _update_height(self):
        if self._updating_height:
            return
        self._updating_height = True
        try:
            target = self._target_height()
            if self.height() != target:
                self.setFixedHeight(target)
        finally:
            self._updating_height = False

    def resizeEvent(self, event):
        # 记录最新宽度，启动定时器
        self._pending_width = event.size().width()
        self._resize_timer.start(80)
        super().resizeEvent(event)

    def _delayed_update(self):
        """定时器超时时执行高度调整和重绘"""
        if self._pending_width is None:
            return
        width = self._pending_width
        self._pending_width = None
        # 调整高度
        self._update_height()
        # 清除缓存，以便 paintEvent 重新生成缩放图
        self._cached_size = None
        self._cached_pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        rect = self.rect()
        size = rect.size()
        if self._cached_pixmap is None or self._cached_size != size:
            self._cached_size = size
            self._cached_pixmap = self._scaled_pixmap(size.width(), size.height())
        if self._cached_pixmap and not self._cached_pixmap.isNull():
            painter.drawPixmap(rect, self._cached_pixmap)
        painter.end()
        # 确保子类绘制（QLabel 默认无其他绘制，但保留）
        super().paintEvent(event)

    def _scaled_pixmap(self, width, height):
        if width <= 0 or height <= 0:
            return QPixmap()
        resized = self.original_image.resize((width, height), Image.LANCZOS)
        if self.opacity_value != 255:
            mask = Image.new('L', resized.size, self.opacity_value)
            resized.putalpha(mask)
        if resized.mode == 'RGBA':
            qimg = QImage(resized.tobytes("raw", "RGBA"),
                          resized.width, resized.height,
                          resized.width * 4, QImage.Format_RGBA8888)
        else:
            resized = resized.convert('RGB')
            qimg = QImage(resized.tobytes("raw", "RGB"),
                          resized.width, resized.height,
                          resized.width * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())


class ResizableArtworkDisplayerHeight:
    """可随父容器宽度自动缩放并保持宽高比的图片展示器"""
    def __init__(self, parent_widget, artwork_path, opacity="100%"):
        self.parent_widget = parent_widget
        opacity_percentage = int(opacity.strip('%')) / 100
        gray_value = int(opacity_percentage * 255)

        self.label = _ResizableArtworkLabel(parent_widget, artwork_path, gray_value)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            parent_layout.addWidget(self.label)


class ArtworkDisplayer:
    def __init__(self, parent_widget: QWidget, artwork_path: str):
        self.parent_widget = parent_widget
        self.artwork_path = artwork_path
        self.target_width = 1366
        self.target_height = 768

        self.load_and_resize_image()

        self.label = QLabel(parent_widget)
        self.label.setPixmap(self._pixmap)
        self.label.setFixedSize(self.target_width, self.target_height)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            parent_layout.addWidget(self.label)

    def load_and_resize_image(self):
        self.original_image = Image.open(self.artwork_path)
        self.resized_image = self.original_image.resize(
            (self.target_width, self.target_height), Image.LANCZOS
        )
        self.resized_image = self.resized_image.convert('RGB')
        qimg = QImage(self.resized_image.tobytes("raw", "RGB"),
                      self.resized_image.width, self.resized_image.height,
                      self.resized_image.width * 3, QImage.Format_RGB888)
        self._pixmap = QPixmap.fromImage(qimg.copy())


class ImageViewerWithScrollbar:
    def __init__(self, parent_widget: QWidget, parent_width: int,
                 parent_height: int, image_path: str):
        self.parent_widget = parent_widget
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.image_path = image_path

        self.image = Image.open(self.image_path)
        self.original_width, self.original_height = self.image.size

        self.scroll_area = QScrollArea(parent_widget)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            parent_layout.addWidget(self.scroll_area)

        self.resize_image()

    def resize_image(self):
        new_width = self.parent_width
        new_height = int(self.original_height * (new_width / self.original_width))

        resized = self.image.resize((new_width, new_height), Image.LANCZOS)
        resized = resized.convert('RGB')
        qimg = QImage(resized.tobytes("raw", "RGB"),
                      resized.width, resized.height,
                      resized.width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg.copy())
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(new_width, new_height)

    def destroy(self):
        self.scroll_area.deleteLater()


class VideoPlayer:
    def __init__(self, parent_widget: QWidget, video_path: str):
        self.parent_widget = parent_widget
        self.video_path = video_path

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        self.target_width = 1366
        self.target_height = 768

        self.label = QLabel(parent_widget)
        self.label.setFixedSize(self.target_width, self.target_height)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            parent_layout.addWidget(self.label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(25)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.target_width, self.target_height))
            h, w, ch = frame.shape
            qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(qimg.copy()))
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def release(self):
        self.timer.stop()
        self.cap.release()


class ThreadVideoPlayer:
    def __init__(self, parent_widget: QWidget, video_path: str):
        self.parent_widget = parent_widget
        self.video_path = video_path

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        self.target_width = 1366
        self.target_height = 768

        self.label = QLabel(parent_widget)
        self.label.setFixedSize(self.target_width, self.target_height)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            parent_layout.addWidget(self.label)

        self.frame_queue = queue.Queue()
        self._running = True

        self.thread = threading.Thread(target=self._frame_loop, daemon=True)
        self.thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_gui)
        self.timer.start(10)

    def _frame_loop(self):
        while self._running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.target_width, self.target_height))
                h, w, ch = frame.shape
                qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                self.frame_queue.put(QPixmap.fromImage(qimg.copy()))
            else:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            time.sleep(0.04)

    def _update_gui(self):
        try:
            pixmap = self.frame_queue.get_nowait()
            self.label.setPixmap(pixmap)
        except queue.Empty:
            pass

    def release(self):
        self._running = False
        self.timer.stop()
        self.cap.release()


class _ResizeEventFilter(QObject):
    """在父窗口缩放时暂停播放，缩放结束 200ms 后恢复"""
    def __init__(self, player, parent_widget):
        super().__init__(parent_widget)
        self.player = player
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._on_resize_done)
        self.is_resizing = False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            if not self.is_resizing:
                self.is_resizing = True
                self.player.pause_playback()
            self.resize_timer.start(200)
            self.player._resize_video()
        return False

    def _on_resize_done(self):
        self.is_resizing = False
        self.player.resume_playback()


class VideoPlayerWithScrollbar:
    def __init__(self, parent_widget: QWidget, parent_width: int,
                 parent_height: int, video_path: str):
        self.parent_widget = parent_widget
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.video_path = video_path

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        self.original_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.original_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.scroll_area = QScrollArea(parent_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setStyleSheet("background-color: black;")
        self.scroll_area.setWidget(self.label)

        target = _get_layout_target(parent_widget)
        parent_layout = target.layout()
        if parent_layout is not None:
            if isinstance(parent_layout, QGridLayout):
                parent_layout.setRowStretch(0, 1)
                parent_layout.setColumnStretch(0, 1)
                parent_layout.addWidget(self.scroll_area, 0, 0)
            else:
                parent_layout.addWidget(self.scroll_area)

        self.current_frame = None
        self.is_paused = False
        self.resize_filter = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

        self.resize_filter = _ResizeEventFilter(self, parent_widget)
        parent_widget.installEventFilter(self.resize_filter)

    def update_frame(self):
        if self.is_paused:
            return
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._resize_video()
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def _resize_video(self):
        if self.current_frame is None:
            return
        viewport = self.scroll_area.viewport()
        available = viewport.size()
        if available.width() <= 0 or available.height() <= 0:
            return
        h, w, ch = self.current_frame.shape
        qimg = QImage(self.current_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg.copy())
        scaled = pixmap.scaled(available.width(), available.height(),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)

    def pause_playback(self):
        self.is_paused = True
        self.timer.stop()

    def resume_playback(self):
        if self.is_paused:
            self.is_paused = False
            self.timer.start(20)

    def release(self):
        if self.resize_filter is not None:
            self.parent_widget.removeEventFilter(self.resize_filter)
            self.resize_filter.deleteLater()
            self.resize_filter = None
        self.timer.stop()
        self.cap.release()


class WrappedLabel(QLabel):
    """自动换行并根据宽度调整高度的标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # Preferred 替代 Expanding，避免 Grid 拉伸冲突
        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        self.setMinimumHeight(1)
        self._last_width = -1

    def heightForWidth(self, width):
        if width <= 0:
            return 1
        margins = self.contentsMargins()
        effective_width = width - margins.left() - margins.right()
        if effective_width <= 0:
            effective_width = 1
        fm = self.fontMetrics()
        rect = fm.boundingRect(
            QRect(0, 0, effective_width, 10000),
            Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop,
            self.text()
        )
        return max(1, rect.height() + margins.top() + margins.bottom())

    def minimumSizeHint(self):
        # 始终基于合理的最小宽度计算，而非当前宽度
        # min_w = 150  # 根据实际业务调整
        min_w = 500
        return QSize(min_w, self.heightForWidth(min_w))

    def hasHeightForWidth(self):
        return True

    def resizeEvent(self, event):
        new_width = event.size().width()
        # 宽度变化时重新计算并更新最小高度
        if abs(new_width - self._last_width) > 1:
            self._last_width = new_width
            target_h = self.heightForWidth(new_width)
            self.setMinimumHeight(target_h)
            self.setMaximumHeight(target_h)  # 同时限制最大高度，防止残留空白
        super().resizeEvent(event)


class BackgroundFrame(QWidget):
    """带背景图片的容器，子控件会显示在背景之上"""
    def __init__(self, parent_widget: QWidget, image_path: str, opacity: str = "100%"):
        super().__init__(parent_widget)
        self._original_pixmap = QPixmap(image_path)
        opacity_percentage = int(opacity.strip('%')) / 100
        self.opacity_value = opacity_percentage

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # ---- 新增防抖定时器 ----
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._delayed_update)
        self._pending_size = None          # 记录最新尺寸
        self._cached_pixmap = None
        self._cached_size = None

        self.setStyleSheet("""
            BackgroundFrame {
                background-color: transparent;
            }
            QGroupBox {
                background-color: transparent;
                border: 1px solid rgba(200, 200, 200, 120);
                border-radius: 6px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 8px;
                background-color: rgba(255, 255, 255, 160);
                border-radius: 4px;
                color: #222222;
                font-weight: bold;
            }
            QLabel {
                background-color: transparent;
                color: #222222;
                font-weight: bold;
            }
        """)

        self._cached_pixmap = None
        self._cached_size = None


    def resizeEvent(self, event):
        # 记录最新尺寸，启动/重置定时器
        self._pending_size = event.size()
        self._resize_timer.start(80)       # 80ms 防抖，可根据体验调整
        super().resizeEvent(event)

    def _delayed_update(self):
        """定时器超时时执行真正的缩放并重绘"""
        if self._pending_size is None:
            return
        size = self._pending_size
        self._pending_size = None
        # 更新缓存的缩放图
        frame_w, frame_h = size.width(), size.height()
        if frame_w <= 0 or frame_h <= 0:
            return
        # 只当尺寸变化时才重新缩放
        if self._cached_size != (frame_w, frame_h):
            self._cached_size = (frame_w, frame_h)
            self._cached_pixmap = self._original_pixmap.scaled(
                frame_w, frame_h,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
        self.update()   # 触发 paintEvent

    def paintEvent(self, event):
        if self._cached_pixmap is None or self._cached_pixmap.isNull():
            super().paintEvent(event)
            return
        painter = QPainter(self)
        if not painter.isActive():
            return
        rect = self.rect()
        frame_w, frame_h = rect.width(), rect.height()
        # 计算偏移居中
        offset_x = (self._cached_pixmap.width() - frame_w) // 2
        offset_y = (self._cached_pixmap.height() - frame_h) // 2
        painter.setOpacity(self.opacity_value)
        painter.drawPixmap(rect, self._cached_pixmap,
                           QRect(offset_x, offset_y, frame_w, frame_h))
        painter.end()
        # 确保子控件正常绘制（调用父类）
        super().paintEvent(event)