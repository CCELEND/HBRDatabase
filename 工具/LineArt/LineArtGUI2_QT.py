# pip install PyQt5 opencv-python numpy
import sys
import os
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFileDialog, QMessageBox,
    QGroupBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFormLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QByteArray, QBuffer, QIODevice, QTimer, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QWheelEvent, QFont


# 图像处理工作线程
class ImageProcessWorker(QThread):
    finished = pyqtSignal(np.ndarray)  # 返回numpy数组
    error = pyqtSignal(str)

    def __init__(self, input_path, min_radius, brightness_offset, enhance_mode, invert=False):
        super().__init__()
        self.input_path = input_path
        self.min_radius = min_radius
        self.brightness_offset = brightness_offset
        self.enhance_mode = enhance_mode
        self.invert = invert

    def run(self):
        try:
            data = np.fromfile(self.input_path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("无法解码图片，请检查文件是否损坏")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            inverted = 255 - gray
            kernel_size = 2 * self.min_radius + 1
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            inverted_min = cv2.erode(inverted, kernel, anchor=(-1, -1), borderType=cv2.BORDER_REPLICATE)
            result = cv2.add(gray, inverted_min)

            # 亮度补偿
            offset = (self.brightness_offset - 50) * 1.0
            if offset != 0:
                result = np.clip(result.astype(np.int16) + offset, 0, 255).astype(np.uint8)

            # 清晰度增强
            if self.enhance_mode == 1:  # 对比度拉伸
                p_low, p_high = np.percentile(result, (2, 98))
                if p_high > p_low:
                    result = np.clip((result - p_low) / (p_high - p_low) * 255, 0, 255).astype(np.uint8)
            elif self.enhance_mode == 2:  # 轻度锐化
                gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=1.5)
                result = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
                result = np.clip(result, 0, 255).astype(np.uint8)
            elif self.enhance_mode == 3:  # 强锐化+去噪
                kernel_open = np.ones((2, 2), np.uint8)
                result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel_open)
                gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=2.0)
                result = cv2.addWeighted(result, 2.0, gaussian, -1.0, 0)
                result = np.clip(result, 0, 255).astype(np.uint8)

            if self.invert:
                result = 255 - result

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# 图片查看器
class ImageViewer(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        # 让pixmap缩放时使用平滑插值
        self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        # 额外开启抗锯齿渲染，线条更圆滑
        self.setRenderHint(QPainter.Antialiasing)

        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.white)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)

        self._zoom_factor = 1.0
        self._min_zoom = 0.05
        self._max_zoom = 20.0
        self._image_loaded = False
        self._user_zoomed = False  # 记是否手动缩放

    def set_image_from_array(self, np_array: np.ndarray):
        # 从numpy数组设置图片，加载时自动适配
        if np_array.ndim == 2:
            h, w = np_array.shape
            qimg = QImage(np_array.data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w, ch = np_array.shape
            rgb = cv2.cvtColor(np_array, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg.copy())
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, w, h)
        self._image_loaded = True
        self._user_zoomed = False  # 新图片加载，重置标志

        QTimer.singleShot(0, self._safe_fit_in_view)

    def _safe_fit_in_view(self):
        if not self._image_loaded:
            return
        rect = self.scene.sceneRect()
        if rect.width() < 1 or rect.height() < 1:
            return
        view_size = self.viewport().size()
        if view_size.width() < 10 or view_size.height() < 10:
            QTimer.singleShot(50, self._safe_fit_in_view)
            return
        self.fitInView(rect, Qt.KeepAspectRatio)
        self._zoom_factor = self.transform().m11()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._image_loaded:
            return

        if not self._user_zoomed:
            # 没有手动缩放过 → 始终跟随窗口大小
            self._safe_fit_in_view()
        else:
            # 手动缩放过 → 只在窗口缩小到看不见图片时才自动缩小
            scene_rect = self.mapFromScene(self.scene.sceneRect()).boundingRect()
            viewport_rect = self.viewport().rect()
            # 如果图片完全在视口外（宽或高都超出），才重新适配
            if (scene_rect.width() > viewport_rect.width() * 1.5 and
                    scene_rect.height() > viewport_rect.height() * 1.5):
                # 仅当窗口明显缩小时才干预，避免正常微调触发
                pass  # 不干预，保持缩放状态
            # 否则完全不干预，保留缩放级别

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        new_zoom = self._zoom_factor * factor
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self.scale(factor, factor)
            self._zoom_factor = new_zoom
            self._user_zoomed = True  # 滚轮缩放

    def mouseDoubleClickEvent(self, event):
        # 双击还原适配
        self._user_zoomed = False  # 双击回到自适应模式
        self._safe_fit_in_view()
        super().mouseDoubleClickEvent(event)


# 主窗口
class LineArtGUI(QMainWindow):
    ENHANCE_MAP = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片转线稿工具 2.0")
        self.resize(750, 320)
        self.input_path = ""
        self.worker = None
        self.preview_window = None
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 文件选择
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("输入图片："))
        self.path_label = QLabel("未选择图片")
        self.path_label.setStyleSheet("color: #666; padding: 4px 8px; background: #f5f5f5; border-radius: 4px;")
        self.path_label.setMinimumWidth(300)
        self.path_label.setToolTip("未选择图片")
        file_layout.addWidget(self.path_label, 1)
        open_btn = QPushButton("打开文件")
        open_btn.setStyleSheet("padding: 6px 16px;")
        open_btn.clicked.connect(self.open_file)
        file_layout.addWidget(open_btn)
        main_layout.addLayout(file_layout)

        # 参数设置区
        param_group = QGroupBox("参数设置（调节线条粗细、明暗及清晰度）")
        param_layout = QFormLayout(param_group)
        param_layout.setSpacing(10)
        param_layout.setContentsMargins(12, 18, 12, 12)

        self.radius_combo = QComboBox()
        self.radius_combo.addItems([str(i) for i in range(1, 11)])
        self.radius_combo.setCurrentIndex(1)  # 默认2
        param_layout.addRow("最小值半径（1~10）：", self.radius_combo)

        self.bright_combo = QComboBox()
        self.bright_combo.addItems([str(i) for i in range(0, 101, 5)])
        self.bright_combo.setCurrentIndex(10)  # 默认50
        param_layout.addRow("亮度补偿（0~100）：", self.bright_combo)

        self.enhance_combo = QComboBox()
        self.enhance_combo.addItems(list(self.ENHANCE_MAP.keys()))
        param_layout.addRow("清晰度增强：", self.enhance_combo)

        main_layout.addWidget(param_group)


        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.preview_btn = QPushButton("预览线稿")
        self.preview_btn.setMinimumSize(140, 38)
        self.preview_btn.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background: #2980b9; }
            QPushButton:disabled { background: #bdc3c7; }
        """)
        self.preview_btn.clicked.connect(self.preview_lineart)
        btn_layout.addWidget(self.preview_btn)

        btn_layout.addSpacing(20)

        self.gen_btn = QPushButton("生成线稿")
        self.gen_btn.setMinimumSize(140, 38)
        self.gen_btn.setStyleSheet("""
            QPushButton { background: #27ae60; color: white; border: none; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background: #219a52; }
            QPushButton:disabled { background: #bdc3c7; }
        """)
        self.gen_btn.clicked.connect(self.generate_lineart)
        btn_layout.addWidget(self.gen_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

    # 文件操作
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if path:
            self.input_path = path
            display = path if len(path) < 50 else "..." + path[-47:]
            self.path_label.setText(display)
            self.path_label.setToolTip(path)

    def _get_params(self):
        return (
            self.input_path,
            int(self.radius_combo.currentText()),
            int(self.bright_combo.currentText()),
            self.ENHANCE_MAP[self.enhance_combo.currentText()]
        )

    # 预览
    def preview_lineart(self):
        if not self.input_path:
            QMessageBox.warning(self, "提示", "请先选择图片！")
            return

        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("预览中...")

        input_path, radius, bright, enhance = self._get_params()
        self.worker = ImageProcessWorker(input_path, radius, bright, enhance)
        self.worker.finished.connect(self._on_preview_ready)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_preview_ready(self, np_array: np.ndarray):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("预览线稿")

        if self.preview_window is None or not self.preview_window.isVisible():
            self.preview_window = PreviewWindow(None)
        self.preview_window.show_image(np_array)
        self.preview_window.show()

        # 强制置顶
        # self.preview_window.raise_()
        # self.preview_window.activateWindow()

    # 保存
    def generate_lineart(self):
        if not self.input_path:
            QMessageBox.warning(self, "提示", "请先选择图片！")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存线稿", "", "PNG图片 (*.png)"
        )
        if not output_path:
            return

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("生成中...")

        input_path, radius, bright, enhance = self._get_params()
        self.worker = ImageProcessWorker(input_path, radius, bright, enhance)
        self.worker.finished.connect(lambda arr: self._on_save_ready(arr, output_path))
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_save_ready(self, np_array: np.ndarray, output_path: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("生成线稿")
        try:
            ext = os.path.splitext(output_path)[1]
            success, buf = cv2.imencode(ext, np_array)
            if success:
                buf.tofile(output_path)
                # QMessageBox.information(self, "成功", f"线稿已保存至：\n{output_path}")
            else:
                QMessageBox.critical(self, "错误", "编码图片失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _on_error(self, msg: str):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("预览线稿")
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("生成线稿")
        QMessageBox.critical(self, "错误", msg)


# 预览窗口
class PreviewWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("线稿预览")
        # 设置较大的默认尺寸和最小尺寸
        self.resize(1000, 900)
        self.setMinimumSize(800, 600)
        self.move(70, 70)

        self.viewer = ImageViewer(self)
        self.setCentralWidget(self.viewer)

        status = QLabel("  滚轮缩放 | 拖拽平移 | 双击还原")
        status.setStyleSheet("background: #ecf0f1; padding: 4px 8px; color: #555; font-size: 12px;")
        from PyQt5.QtWidgets import QStatusBar
        sb = QStatusBar()
        sb.addPermanentWidget(status)
        self.setStatusBar(sb)

    def show_image(self, np_array: np.ndarray):
        self.viewer.set_image_from_array(np_array)

    def closeEvent(self, event):
        event.ignore()
        self.hide()



def load_LineArtGUI2_QT():
    import threading
    browser_thread = threading.Thread(target=run_LineArtGUI2_QT, daemon=False)
    browser_thread.start()

def run_LineArtGUI2_QT():
    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))

    from PyQt5.QtGui import QIcon
    app.setWindowIcon(QIcon("app_icon.png"))

    # 全局样式
    app.setStyleSheet("""
        QMainWindow { background: #ffffff; }
        QGroupBox { font-weight: bold; border: 1px solid #ddd; border-radius: 6px; margin-top: 10px; padding-top: 14px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        QComboBox { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; min-width: 80px; }
        QComboBox:hover { border-color: #3498db; }
        QLabel { font-size: 13px; }
    """)

    window = LineArtGUI()
    window.move(1100, 360)
    window.show()
    sys.exit(app.exec_())