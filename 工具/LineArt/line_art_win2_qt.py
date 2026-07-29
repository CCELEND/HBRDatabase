
import os
import cv2
import numpy as np
import tempfile
import types

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from window_qt import creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from canvas_events_qt import ImageViewerWithScrollbar

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


MONO_FONT = QFont("Microsoft YaHei", 9)


def _ensure_layout(widget):
    layout = widget.layout()
    if layout is None:
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    return layout


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

    def image_to_lineart(self, input_path, output_path, min_radius, brightness_offset,
                         enhance_mode=0, invert=False):
        data = np.fromfile(input_path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法解码图片")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        kernel_size = 2 * min_radius + 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        inverted_min = cv2.erode(inverted, kernel, anchor=(-1, -1), borderType=cv2.BORDER_REPLICATE)
        result = cv2.add(gray, inverted_min)

        offset = (brightness_offset - 50) * 1.0
        if offset != 0:
            result = np.clip(result.astype(np.int16) + offset, 0, 255).astype(np.uint8)

        if enhance_mode == 1:
            p_low, p_high = np.percentile(result, (2, 98))
            if p_high > p_low:
                result = np.clip((result - p_low) / (p_high - p_low) * 255, 0, 255).astype(np.uint8)
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

    def preview_lineart(self):
        input_path = self.input_path
        if input_path == "未选择图片":
            QMessageBox.warning(self.root, "提示", "请先选择图片！")
            win_set_top('图片转线稿工具2.0', __name__)
            return

        radius = int(self.radius_cb.currentText())
        bright = int(self.bright_cb.currentText())
        enhance_str = self.enhance_cb.currentText()
        enhance_map = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}
        enhance = enhance_map.get(enhance_str, 0)

        if self.temp_preview_path is None:
            fd, self.temp_preview_path = tempfile.mkstemp(suffix='.png', prefix='lineart_preview_')
            os.close(fd)

        if self.preview_window is not None and self.preview_window.isVisible():
            try:
                self.preview_btn.setText("预览中...")
                self.preview_btn.setEnabled(False)

                self.image_to_lineart(
                    input_path=input_path,
                    output_path=self.temp_preview_path,
                    min_radius=radius,
                    brightness_offset=bright,
                    enhance_mode=enhance,
                    invert=False
                )
                self.viewer.update_image(self.temp_preview_path)
                self.preview_window.raise_()
                self.preview_window.activateWindow()
            except Exception as e:
                logger.error(str(e))
                QMessageBox.critical(self.root, "错误", f"预览更新失败：{str(e)}")
            finally:
                self.preview_btn.setText("预览线稿")
                self.preview_btn.setEnabled(True)
            return

        try:
            self.preview_btn.setText("预览中...")
            self.preview_btn.setEnabled(False)

            self.image_to_lineart(
                input_path=input_path,
                output_path=self.temp_preview_path,
                min_radius=radius,
                brightness_offset=bright,
                enhance_mode=enhance,
                invert=False
            )

            preview_win = creat_Toplevel("线稿预览", 1000, 900, 70, 70)
            preview_frame = QWidget(preview_win)
            preview_win.setCentralWidget(preview_frame)
            frame_layout = QGridLayout(preview_frame)
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame_layout.setSpacing(0)

            viewer = ImageViewerWithScrollbar(preview_frame, 1000, 900, self.temp_preview_path)

            self.preview_window = preview_win
            self.viewer = viewer

            def on_close(self, event):
                self.viewer.destroy()
                self.preview_window = None
                self.viewer = None
                event.accept()
            preview_win.closeEvent = types.MethodType(on_close, preview_win)

        except Exception as e:
            logger.error(str(e))
            QMessageBox.critical(self.root, "错误", f"预览失败：{str(e)}")
        finally:
            self.preview_btn.setText("预览线稿")
            self.preview_btn.setEnabled(True)

    def generate_lineart(self):
        input_path = self.input_path
        if input_path == "未选择图片":
            QMessageBox.warning(self.root, "提示", "请先选择图片！")
            win_set_top('图片转线稿工具2.0', __name__)
            return

        radius = int(self.radius_cb.currentText())
        bright = int(self.bright_cb.currentText())
        enhance_str = self.enhance_cb.currentText()
        enhance_map = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}
        enhance = enhance_map.get(enhance_str, 0)

        output_path, _ = QFileDialog.getSaveFileName(
            self.root,
            "保存线稿",
            "",
            "PNG图片 (*.png)"
        )
        if not output_path:
            return

        try:
            self.gen_btn.setText("生成中...")
            self.gen_btn.setEnabled(False)

            self.image_to_lineart(
                input_path=input_path,
                output_path=output_path,
                min_radius=radius,
                brightness_offset=bright,
                enhance_mode=enhance,
                invert=False
            )
            win_set_top('图片转线稿工具2.0', __name__)
        except Exception as e:
            logger.error(str(e))
            QMessageBox.critical(self.root, "错误", f"生成失败：{str(e)}")
            win_set_top('图片转线稿工具2.0', __name__)
        finally:
            self.gen_btn.setText("生成线稿")
            self.gen_btn.setEnabled(True)


def creat_line_art_win2():
    if is_win_open('图片转线稿工具2.0', __name__):
        win_set_top('图片转线稿工具2.0', __name__)
        return "break"

    line_art_win_frame = creat_Toplevel("图片转线稿工具2.0", 695, 280, 1100, 360)
    gui = LineArtGUI2(line_art_win_frame)

    win_open_manage(line_art_win_frame, __name__)
    line_art_win_frame.closeEvent = lambda ev: (win_close_manage(line_art_win_frame, __name__), ev.accept())

