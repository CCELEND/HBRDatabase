
import os
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from window_qt import creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


MONO_FONT = QFont("Microsoft YaHei", 9)

# 持有 worker，避免 QThread 被 GC
_LIVE_WORKERS = set()


def _image_to_lineart(input_path, output_path, line_thickness,
                      threshold1, threshold2, invert=False):
    data = np.fromfile(input_path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k = max(1, int(line_thickness) | 1)  # 高斯核需为正奇数
    blurred = cv2.GaussianBlur(gray, (k, k), 0)
    edges = cv2.Canny(blurred, threshold1=int(threshold1), threshold2=int(threshold2))
    if not invert:
        edges = cv2.bitwise_not(edges)

    cv2.imencode('.png', edges)[1].tofile(output_path)


class _LineArtWorker(QThread):
    done = pyqtSignal(str)   # output_path
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, line_thickness,
                 threshold1, threshold2, invert=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.line_thickness = line_thickness
        self.threshold1 = threshold1
        self.threshold2 = threshold2
        self.invert = invert

    def run(self):
        try:
            _image_to_lineart(
                self.input_path, self.output_path,
                self.line_thickness, self.threshold1, self.threshold2,
                self.invert)
            self.done.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


def _ensure_layout(widget):
    layout = widget.layout()
    if layout is None:
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    return layout


class LineArtGUI:
    def __init__(self, root):
        self.root = root
        self.input_path = "未选择图片"
        self.line_thickness = 3
        self.threshold1 = 30
        self.threshold2 = 80
        self._worker = None
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

        param_frame = QGroupBox("参数设置（数值越小细节越多，但是噪声会更多）")
        param_layout = QGridLayout(param_frame)
        param_layout.setContentsMargins(15, 15, 15, 15)
        param_layout.setSpacing(8)

        param_layout.addWidget(QLabel("高斯模糊核大小"), 0, 0)
        self.thickness_cb = QComboBox()
        self.thickness_cb.addItems([str(i) for i in range(1, 11)])
        self.thickness_cb.setCurrentText(str(self.line_thickness))
        param_layout.addWidget(self.thickness_cb, 0, 1)

        param_layout.addWidget(QLabel("Canny算子低阈值(10-300)"), 0, 2)
        self.t1_cb = QComboBox()
        self.t1_cb.addItems([str(i) for i in range(10, 301, 10)])
        self.t1_cb.setCurrentText(str(self.threshold1))
        param_layout.addWidget(self.t1_cb, 0, 3)

        param_layout.addWidget(QLabel("Canny算子高阈值(10-300)"), 1, 0)
        self.t2_cb = QComboBox()
        self.t2_cb.addItems([str(i) for i in range(10, 301, 10)])
        self.t2_cb.setCurrentText(str(self.threshold2))
        param_layout.addWidget(self.t2_cb, 1, 1)

        layout.addWidget(param_frame, 1, 0)

        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(10, 5, 10, 10)
        btn_layout.setSpacing(5)
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
            win_set_top('图片转线稿工具', __name__)
            self.input_path = path
            self.path_entry.setText(path)
            self.path_entry.setToolTip(path)

    def generate_lineart(self):
        input_path = self.input_path
        if input_path == "未选择图片":
            QMessageBox.warning(self.root, "提示", "请先选择图片！")
            win_set_top('图片转线稿工具', __name__)
            return

        if self._worker is not None and self._worker.isRunning():
            return

        lt = int(self.thickness_cb.currentText())
        t1 = int(self.t1_cb.currentText())
        t2 = int(self.t2_cb.currentText())

        output_path, _ = QFileDialog.getSaveFileName(
            self.root,
            "保存线稿",
            "",
            "PNG图片 (*.png)"
        )
        if not output_path:
            return

        self.gen_btn.setText("生成中...")
        self.gen_btn.setEnabled(False)
        worker = _LineArtWorker(input_path, output_path, lt, t1, t2, invert=False)
        self._worker = worker
        _LIVE_WORKERS.add(worker)

        def on_done(path):
            _LIVE_WORKERS.discard(worker)
            worker.deleteLater()
            if self._worker is worker:
                self._worker = None
            win_set_top('图片转线稿工具', __name__)
            self.gen_btn.setText("生成线稿")
            self.gen_btn.setEnabled(True)

        def on_error(msg):
            _LIVE_WORKERS.discard(worker)
            worker.deleteLater()
            if self._worker is worker:
                self._worker = None
            logger.error(msg)
            QMessageBox.critical(self.root, "错误", f"生成失败：{msg}")
            win_set_top('图片转线稿工具', __name__)
            self.gen_btn.setText("生成线稿")
            self.gen_btn.setEnabled(True)

        worker.done.connect(on_done)
        worker.error.connect(on_error)
        worker.start()


def creat_line_art_win():
    if is_win_open('图片转线稿工具', __name__):
        win_set_top('图片转线稿工具', __name__)
        return "break"

    line_art_win_frame = creat_Toplevel("图片转线稿工具", 695, 280, 500, 300)
    gui = LineArtGUI(line_art_win_frame)

    win_open_manage(line_art_win_frame, __name__)

    # 正确关闭事件
    def on_close(ev):
        if gui._worker is not None:
            gui._worker.wait(2000)
        win_close_manage(line_art_win_frame, __name__)
        ev.accept()
    line_art_win_frame.closeEvent = on_close

    return "break"
