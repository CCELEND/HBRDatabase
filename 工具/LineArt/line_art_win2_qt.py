
import os
import cv2
import numpy as np
import tempfile

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from window_qt import creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from canvas_events_qt import ImageViewerWithScrollbar

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


MONO_FONT = QFont("Microsoft YaHei", 9)
_ENHANCE_MAP = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}
_LIVE_WORKERS = set()


def _ensure_layout(widget):
    layout = widget.layout()
    if layout is None:
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    return layout


def _image_to_lineart(input_path, output_path, min_radius, brightness_offset,
                      enhance_mode=0, invert=False):
    data = np.fromfile(input_path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inverted = 255 - gray
    kernel_size = 2 * min_radius + 1
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    inverted_min = cv2.erode(inverted, kernel, anchor=(-1, -1),
                             borderType=cv2.BORDER_REPLICATE)
    result = cv2.add(gray, inverted_min)

    offset = (brightness_offset - 50) * 1.0
    if offset != 0:
        result = np.clip(result.astype(np.int16) + offset, 0, 255).astype(np.uint8)

    if enhance_mode == 1:
        p_low, p_high = np.percentile(result, (2, 98))
        if p_high > p_low:
            result = np.clip((result - p_low) / (p_high - p_low) * 255,
                             0, 255).astype(np.uint8)
    elif enhance_mode == 2:
        gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=1.5)
        result = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
        result = np.clip(result, 0, 255).astype(np.uint8)
    elif enhance_mode == 3:
        kernel_open = np.ones((2, 2), np.uint8)
        result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel_open)
        gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=2.0)
        result = cv2.addWeighted(result, 2.0, gaussian, -1.0, 0)
        result = np.clip(result, 0, 255).astype(np.uint8)

    if invert:
        result = 255 - result

    cv2.imencode('.png', result)[1].tofile(output_path)
    return output_path


class _LineArtWorker2(QThread):
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, min_radius, brightness_offset,
                 enhance_mode=0, invert=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.min_radius = min_radius
        self.brightness_offset = brightness_offset
        self.enhance_mode = enhance_mode
        self.invert = invert

    def run(self):
        try:
            _image_to_lineart(
                self.input_path, self.output_path,
                self.min_radius, self.brightness_offset,
                self.enhance_mode, self.invert)
            self.done.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class LineArtGUI2:
    def __init__(self, root):
        self.root = root
        self.input_path = "未选择图片"
        self.min_radius = 2
        self.brightness_offset = 50
        self.enhance_mode = "无"
        self.preview_window = None
        self.viewer = None
        self.temp_preview_path = None
        self._preview_worker = None
        self._gen_worker = None
        self.create_widgets()

    def create_widgets(self):
        central = self.root.centralWidget()
        layout = _ensure_layout(central)

        file_frame = QWidget()
        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(10, 10, 10, 5)
        file_layout.setSpacing(5)

        file_layout.addWidget(QLabel("输入图片："))

        self.path_entry = QLineEdit()
        self.path_entry.setText(self.input_path)
        self.path_entry.setReadOnly(True)
        self.path_entry.setToolTip(self.input_path)
        file_layout.addWidget(self.path_entry)

        open_btn = QPushButton("打开文件")
        open_btn.clicked.connect(self.open_file)
        file_layout.addWidget(open_btn)

        layout.addWidget(file_frame, 0, 0)

        param_frame = QGroupBox("参数设置（调节线条粗细、明暗及清晰度）")
        param_layout = QGridLayout(param_frame)
        param_layout.setContentsMargins(12, 12, 12, 12)
        param_layout.setSpacing(6)

        param_layout.addWidget(QLabel("最小值半径（1~10）"), 0, 0)
        self.radius_cb = QComboBox()
        self.radius_cb.addItems([str(i) for i in range(1, 11)])
        self.radius_cb.setCurrentText(str(self.min_radius))
        param_layout.addWidget(self.radius_cb, 0, 1)

        param_layout.addWidget(QLabel("亮度补偿（0~100）"), 0, 2)
        self.bright_cb = QComboBox()
        self.bright_cb.addItems([str(i) for i in range(0, 101, 5)])
        self.bright_cb.setCurrentText(str(self.brightness_offset))
        param_layout.addWidget(self.bright_cb, 0, 3)

        param_layout.addWidget(QLabel("清晰度增强："), 1, 0)
        self.enhance_cb = QComboBox()
        self.enhance_cb.addItems(["无", "对比度拉伸", "轻度锐化", "强锐化+去噪"])
        self.enhance_cb.setCurrentText(self.enhance_mode)
        param_layout.addWidget(self.enhance_cb, 1, 1, 1, 3)

        layout.addWidget(param_frame, 1, 0)

        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(10, 5, 10, 10)
        btn_layout.setSpacing(5)

        self.preview_btn = QPushButton("预览线稿")
        self.preview_btn.setFixedWidth(120)
        self.preview_btn.clicked.connect(self.preview_lineart)
        btn_layout.addWidget(self.preview_btn)

        btn_layout.addStretch()

        self.gen_btn = QPushButton("生成线稿")
        self.gen_btn.setFixedWidth(120)
        self.gen_btn.clicked.connect(self.generate_lineart)
        btn_layout.addWidget(self.gen_btn)

        layout.addWidget(btn_frame, 2, 0)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.root,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if path:
            win_set_top('图片转线稿工具2.0', __name__)
            self.input_path = path
            self.path_entry.setText(path)
            self.path_entry.setToolTip(path)

    def _params(self):
        radius = int(self.radius_cb.currentText())
        bright = int(self.bright_cb.currentText())
        enhance = _ENHANCE_MAP.get(self.enhance_cb.currentText(), 0)
        return radius, bright, enhance

    def _destroy_preview(self):
        """关闭并释放预览窗口（不删除临时文件）。"""
        preview = self.preview_window
        self.preview_window = None
        if preview is not None:
            try:
                preview.close()
            except RuntimeError:
                pass
        # 预览窗口的 closeEvent 正常会销毁 viewer；这里兜底
        viewer = self.viewer
        self.viewer = None
        if viewer is not None:
            try:
                viewer.destroy()
            except RuntimeError:
                pass

    def cleanup(self):
        """主窗口关闭时释放预览窗口和临时预览文件。"""
        for worker in (self._preview_worker, self._gen_worker):
            if worker is not None:
                try:
                    worker.wait(2000)
                except Exception:
                    pass
        self._destroy_preview()
        path = self.temp_preview_path
        self.temp_preview_path = None
        if path:
            try:
                os.remove(path)
            except OSError:
                pass

    def _start_worker(self, worker, on_ok, on_err, btn, busy_text, idle_text):
        _LIVE_WORKERS.add(worker)
        btn.setText(busy_text)
        btn.setEnabled(False)

        def _finish():
            _LIVE_WORKERS.discard(worker)
            worker.deleteLater()
            btn.setText(idle_text)
            btn.setEnabled(True)

        def ok(path):
            _finish()
            on_ok(path)

        def err(msg):
            _finish()
            on_err(msg)

        worker.done.connect(ok)
        worker.error.connect(err)
        worker.start()
        return worker

    def preview_lineart(self):
        input_path = self.input_path
        if input_path == "未选择图片":
            QMessageBox.warning(self.root, "提示", "请先选择图片！")
            win_set_top('图片转线稿工具2.0', __name__)
            return

        if self._preview_worker is not None and self._preview_worker.isRunning():
            return

        radius, bright, enhance = self._params()
        if self.temp_preview_path is None:
            fd, self.temp_preview_path = tempfile.mkstemp(
                suffix='.png', prefix='lineart_preview_')
            os.close(fd)

        output_path = self.temp_preview_path
        worker = _LineArtWorker2(
            input_path, output_path, radius, bright, enhance, invert=False)
        self._preview_worker = worker

        def on_ok(path):
            try:
                if self.preview_window is None:
                    preview_win = creat_Toplevel("线稿预览", 1000, 900, 70, 70)
                    preview_frame = QWidget(preview_win)
                    preview_win.setCentralWidget(preview_frame)
                    frame_layout = QGridLayout(preview_frame)
                    frame_layout.setContentsMargins(0, 0, 0, 0)
                    frame_layout.setSpacing(0)

                    viewer = ImageViewerWithScrollbar(
                        preview_frame, 1000, 900, path)
                    self.preview_window = preview_win
                    self.viewer = viewer

                    def on_close(event):
                        try:
                            viewer.destroy()
                        finally:
                            self.preview_window = None
                            self.viewer = None
                        event.accept()
                    preview_win.closeEvent = on_close
                    preview_win.show()
                else:
                    if self.viewer is not None:
                        self.viewer.image_label.close_image()
                        self.viewer.image_label.original_image = None
                        from PIL import Image
                        self.viewer.image_label.original_image = Image.open(path)
                        self.viewer.image_label.refresh()
                    self.preview_window.show()
                    self.preview_window.raise_()
                    self.preview_window.activateWindow()
            except Exception as e:
                logger.error(str(e))
                QMessageBox.critical(self.root, "错误", f"预览失败：{str(e)}")

        def on_err(msg):
            logger.error(msg)
            QMessageBox.critical(self.root, "错误", f"预览失败：{msg}")

        self._start_worker(worker, on_ok, on_err,
                           self.preview_btn, "预览中...", "预览线稿")

    def generate_lineart(self):
        input_path = self.input_path
        if input_path == "未选择图片":
            QMessageBox.warning(self.root, "提示", "请先选择图片！")
            win_set_top('图片转线稿工具2.0', __name__)
            return

        if self._gen_worker is not None and self._gen_worker.isRunning():
            return

        radius, bright, enhance = self._params()
        output_path, _ = QFileDialog.getSaveFileName(
            self.root, "保存线稿", "", "PNG图片 (*.png)")
        if not output_path:
            return

        worker = _LineArtWorker2(
            input_path, output_path, radius, bright, enhance, invert=False)
        self._gen_worker = worker

        def on_ok(_path):
            win_set_top('图片转线稿工具2.0', __name__)

        def on_err(msg):
            logger.error(msg)
            QMessageBox.critical(self.root, "错误", f"生成失败：{msg}")
            win_set_top('图片转线稿工具2.0', __name__)

        self._start_worker(worker, on_ok, on_err,
                           self.gen_btn, "生成中...", "生成线稿")


def creat_line_art_win2():
    if is_win_open('图片转线稿工具2.0', __name__):
        win_set_top('图片转线稿工具2.0', __name__)
        return "break"

    line_art_win_frame = creat_Toplevel("图片转线稿工具2.0", 695, 280, 1100, 360)
    gui = LineArtGUI2(line_art_win_frame)

    win_open_manage(line_art_win_frame, __name__)

    def on_close(ev):
        gui.cleanup()
        win_close_manage(line_art_win_frame, __name__)
        ev.accept()

    line_art_win_frame.closeEvent = on_close
    return "break"
