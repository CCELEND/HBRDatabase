# -*- coding: utf-8 -*-
# pip install PyQt5 opencv-python numpy
"""视频转线稿工具。

把整段视频逐帧转成线稿，输出：

* MP4 线稿视频（H.264，可保留原视频音频；需要系统里有 ffmpeg）
* MP4 线稿视频（OpenCV 内置编码，无需 ffmpeg）
* PNG 帧序列（存到一个文件夹里）

线稿算法与「图片转线稿工具 2.0」完全一致，见 :mod:`工具.LineArt.line_art_core`。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

# 允许直接从本文件所在目录运行（此时不在仓库根目录，补一下 sys.path）
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cv2
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QRadioButton, QSlider, QStatusBar, QVBoxLayout, QWidget
)

from 工具.LineArt.line_art_core import ENHANCE_MAP, VIDEO_EXTS, to_line_art
from 工具.LineArt.LineArtGUI2_QT import ImageViewer

# 让 ffmpeg 子进程不弹出黑色控制台窗口（Windows）
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# 输出方式
OUT_H264 = "h264"    # ffmpeg 编码 H.264，画质好、体积小，可带音频
OUT_MP4V = "mp4v"    # OpenCV 内置编码，任何环境都能用，无音频
OUT_PNG = "png"      # PNG 帧序列


def find_ffmpeg() -> str:
    """找一个可用的 ffmpeg（优先 PATH）。"""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    for cand in (r"F:\tool\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",):
        if os.path.exists(cand):
            return cand
    return ""


def _fmt_time(sec) -> str:
    """把秒数格式化成 12:34 / 1:02:03。"""
    try:
        sec = int(round(float(sec)))
    except (TypeError, ValueError):
        return "--:--"
    if sec < 0:
        return "--:--"
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%02d:%02d" % (m, s)


def _remux_with_audio(ffmpeg: str, video_path: str, audio_src: str, out_path: str) -> bool:
    """把无声线稿视频 + 原视频的音频合并（视频流直接 copy，不重新编码）。"""
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path, "-i", audio_src,
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", out_path,
    ]
    try:
        r = subprocess.run(cmd, creationflags=_NO_WINDOW,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode == 0 and os.path.exists(out_path)
    except Exception:
        return False


class FramePreviewWorker(QThread):
    """读取视频中的某一帧并转成线稿（用于参数预览）。"""

    frame_ready = pyqtSignal(int, object)   # (请求序号, 线稿数组)
    error = pyqtSignal(str)

    def __init__(self, video_path, frame_index, params, seq):
        super().__init__()
        self.video_path = video_path
        self.frame_index = frame_index
        self.params = params
        self.seq = seq

    def run(self):
        cap = None
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
            if self.frame_index > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
            ok, frame = cap.read()
            if not ok or frame is None:
                raise ValueError("读取第 %d 帧失败" % (self.frame_index + 1))
            self.frame_ready.emit(self.seq, to_line_art(frame, **self.params))
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if cap is not None:
                cap.release()


class _Cancelled(Exception):
    """内部信号：用户取消了转换。"""


class ConvertWorker(QThread):
    """逐帧转换整段视频。"""

    progress = pyqtSignal(int, int)      # (已处理帧数, 总帧数，0 表示未知)
    sampled = pyqtSignal(object)         # 抽样预览帧
    status = pyqtSignal(str)
    finished_ok = pyqtSignal(str)        # 输出路径
    cancelled = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, video_path, out_path, out_mode, params, scale,
                 keep_audio, ffmpeg):
        super().__init__()
        self.video_path = video_path
        self.out_path = out_path
        self.out_mode = out_mode
        self.params = params
        self.scale = scale
        self.keep_audio = keep_audio
        self.ffmpeg = ffmpeg
        self.tmp_path = ""
        self._cancel = False

    def cancel(self):
        self._cancel = True

    # ---- 内部工具 ----
    def _remove_quiet(self, path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def run(self):
        cap = None
        writer = None
        proc = None
        err_file = None
        written = []          # 已写出的 PNG（取消/失败时删除）
        idx = 0
        total = 0
        ok_done = False       # 成功产出后置 True，避免 finally 误删结果
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise ValueError("无法打开视频，请检查文件是否损坏或缺少解码器")

            fps = cap.get(cv2.CAP_PROP_FPS)
            if not fps or fps <= 0 or fps != fps:
                fps = 25.0
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            w0 = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            h0 = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            if w0 <= 0 or h0 <= 0:
                raise ValueError("读取视频分辨率失败")

            out_w = max(2, int(round(w0 * self.scale)))
            out_h = max(2, int(round(h0 * self.scale)))
            if self.out_mode == OUT_H264:      # yuv420p 要求宽高都是偶数
                out_w -= out_w % 2
                out_h -= out_h % 2

            self.status.emit("准备输出...")
            self.progress.emit(0, total)

            if self.out_mode == OUT_PNG:
                os.makedirs(self.out_path, exist_ok=True)
            elif self.out_mode == OUT_H264:
                cmd = [
                    self.ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "rawvideo", "-pix_fmt", "gray",
                    "-s", "%dx%d" % (out_w, out_h),
                    "-r", "%.6f" % fps, "-i", "-",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", self.tmp_path,
                ]
                err_file = tempfile.TemporaryFile()
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                        stdout=subprocess.DEVNULL,
                                        stderr=err_file,
                                        creationflags=_NO_WINDOW)
            else:
                writer = cv2.VideoWriter(
                    self.tmp_path, cv2.VideoWriter_fourcc(*"mp4v"),
                    fps, (out_w, out_h))
                if not writer.isOpened():
                    raise ValueError("无法创建输出视频文件")

            sample_step = max(1, total // 60) if total > 0 else 30
            prog_step = max(1, total // 200) if total > 0 else 5
            self.status.emit("开始转换...")

            while True:
                if self._cancel:
                    break
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                if frame.shape[1] != out_w or frame.shape[0] != out_h:
                    frame = cv2.resize(frame, (out_w, out_h),
                                       interpolation=cv2.INTER_AREA)
                gray = to_line_art(frame, **self.params)

                if self.out_mode == OUT_PNG:
                    ok2, buf = cv2.imencode(".png", gray)
                    if not ok2:
                        raise ValueError("PNG 编码失败")
                    name = "frame_%06d.png" % (idx + 1)
                    buf.tofile(os.path.join(self.out_path, name))
                    written.append(name)
                elif self.out_mode == OUT_H264:
                    proc.stdin.write(gray.tobytes())
                else:
                    writer.write(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))

                idx += 1
                if idx % prog_step == 0:
                    self.progress.emit(idx, total)
                if idx % sample_step == 0:
                    self.sampled.emit(gray)

            self.progress.emit(idx, total)

            # ---- 收尾 ----
            if self._cancel:
                raise _Cancelled()

            cap.release()
            cap = None

            if self.out_mode == OUT_H264:
                proc.communicate()
                rc = proc.returncode
                err_file.seek(0)
                err_b = err_file.read()
                err_file.close()
                err_file = None
                proc = None
                if rc != 0:
                    raise ValueError("ffmpeg 编码失败(code=%s)：%s"
                                     % (rc, err_b.decode("utf-8", "replace")[:300].strip()))
            elif writer is not None:
                writer.release()
                writer = None

            if idx == 0:
                raise ValueError("没有读到任何视频帧")

            if self.out_mode == OUT_PNG:
                ok_done = True
                self.finished_ok.emit(self.out_path)
                return

            # 视频文件：需要时把原视频的音频合并进来
            if self.keep_audio and self.ffmpeg:
                if _remux_with_audio(self.ffmpeg, self.tmp_path,
                                     self.video_path, self.out_path):
                    self._remove_quiet(self.tmp_path)
                    ok_done = True
                    self.finished_ok.emit(self.out_path)
                    return
                self.status.emit("音频合并失败，已输出无声版本")
            os.replace(self.tmp_path, self.out_path)
            ok_done = True
            self.finished_ok.emit(self.out_path)

        except _Cancelled:
            self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # 先释放句柄（ffmpeg 还占着文件时删不掉），再清理没成功的临时产物
            if cap is not None:
                cap.release()
            if writer is not None:
                writer.release()
            if proc is not None:
                if proc.poll() is None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    try:
                        proc.wait(timeout=3)
                    except Exception:
                        pass
            if err_file is not None:
                try:
                    err_file.close()
                except Exception:
                    pass
            if not ok_done:
                self._remove_quiet(self.tmp_path)
                for name in written:
                    self._remove_quiet(os.path.join(self.out_path, name))


class PreviewWindow(QMainWindow):
    """线稿预览窗口（滚轮缩放 / 拖拽平移 / 双击还原）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("线稿预览")
        self.resize(1000, 900)
        self.setMinimumSize(640, 480)
        self.move(70, 70)

        self.viewer = ImageViewer(self)
        self.setCentralWidget(self.viewer)

        tip = QLabel("  滚轮缩放 | 拖拽平移 | 双击还原")
        tip.setStyleSheet("background: #ecf0f1; padding: 4px 8px; color: #555; font-size: 12px;")
        sb = QStatusBar()
        sb.addPermanentWidget(tip)
        self.setStatusBar(sb)

    def show_image(self, np_array):
        self.viewer.set_image_from_array(np_array)


class VideoLineArtGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频转线稿工具")
        self.resize(860, 560)
        self.setAcceptDrops(True)

        self.video_path = ""
        self.meta = None            # (fps, 总帧数, 宽, 高)
        self.ffmpeg = find_ffmpeg()
        self.preview_window = None
        self._frame_workers = set()
        self._preview_seq = 0
        self._last_shown_seq = -1
        self.convert_worker = None
        self.out_path = ""
        self._t0 = 0.0

        self._init_ui()
        self._refresh_output_state()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        # --- 输入视频 ---
        row = QHBoxLayout()
        row.addWidget(QLabel("输入视频："))
        self.path_label = QLabel("未选择视频（也可以把视频文件拖进来）")
        self.path_label.setStyleSheet(
            "color: #666; padding: 4px 8px; background: #f5f5f5; border-radius: 4px;")
        self.path_label.setMinimumWidth(360)
        self.path_label.setToolTip("")
        row.addWidget(self.path_label, 1)
        self.open_btn = QPushButton("打开文件")
        self.open_btn.setStyleSheet("padding: 6px 16px;")
        self.open_btn.clicked.connect(self.pick_video)
        row.addWidget(self.open_btn)
        root.addLayout(row)

        self.info_label = QLabel(" ")
        self.info_label.setStyleSheet("color: #888; font-size: 12px;")
        root.addWidget(self.info_label)

        # --- 参数设置 ---
        param_group = QGroupBox("参数设置（调节线条粗细、明暗及清晰度）")
        form = QFormLayout(param_group)
        form.setSpacing(10)
        form.setContentsMargins(12, 18, 12, 12)

        self.radius_combo = QComboBox()
        self.radius_combo.addItems([str(i) for i in range(1, 11)])
        self.radius_combo.setCurrentIndex(1)          # 默认 2
        form.addRow("最小值半径（1~10）：", self.radius_combo)

        self.bright_combo = QComboBox()
        self.bright_combo.addItems([str(i) for i in range(0, 101, 5)])
        self.bright_combo.setCurrentIndex(10)         # 默认 50
        form.addRow("亮度补偿（0~100）：", self.bright_combo)

        self.enhance_combo = QComboBox()
        self.enhance_combo.addItems(list(ENHANCE_MAP.keys()))
        form.addRow("清晰度增强：", self.enhance_combo)

        self.invert_check = QCheckBox("反相输出（黑底白线）")
        form.addRow("", self.invert_check)

        root.addWidget(param_group)

        # --- 输出设置 ---
        out_group = QGroupBox("输出设置")
        out_box = QVBoxLayout(out_group)
        out_box.setContentsMargins(12, 18, 12, 12)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("输出方式："))
        self.radio_h264 = QRadioButton("MP4（H.264，画质好）")
        self.radio_mp4v = QRadioButton("MP4（内置编码，无需 ffmpeg）")
        self.radio_png = QRadioButton("PNG 帧序列")
        self.radio_h264.setChecked(True)
        self.mode_group = QButtonGroup(self)
        for i, rb in enumerate((self.radio_h264, self.radio_mp4v, self.radio_png)):
            self.mode_group.addButton(rb, i)
            rb.toggled.connect(lambda _checked: self._refresh_output_state())
            mode_row.addWidget(rb)
        mode_row.addStretch()
        out_box.addLayout(mode_row)

        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("输出缩放："))
        self.scale_combo = QComboBox()
        for text, val in (("100%（原始）", 1.0), ("75%", 0.75), ("50%", 0.5), ("25%", 0.25)):
            self.scale_combo.addItem(text, val)
        opt_row.addWidget(self.scale_combo)
        self.audio_check = QCheckBox("保留原视频音频（需要 ffmpeg）")
        opt_row.addSpacing(16)
        opt_row.addWidget(self.audio_check)
        opt_row.addStretch()
        out_box.addLayout(opt_row)
        root.addWidget(out_group)

        # --- 预览帧 ---
        prev_row = QHBoxLayout()
        prev_row.addWidget(QLabel("预览帧："))
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.setEnabled(False)
        self.frame_slider.valueChanged.connect(self._on_slider_changed)
        prev_row.addWidget(self.frame_slider, 1)
        self.frame_label = QLabel("第 - / - 帧")
        self.frame_label.setMinimumWidth(120)
        self.frame_label.setStyleSheet("color: #555;")
        prev_row.addWidget(self.frame_label)
        root.addLayout(prev_row)

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(250)
        self._preview_timer.timeout.connect(lambda: self.preview_frame())

        # --- 按钮 ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.preview_btn = QPushButton("预览此帧线稿")
        self.preview_btn.setMinimumSize(140, 38)
        self.preview_btn.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background: #2980b9; }
            QPushButton:disabled { background: #bdc3c7; }
        """)
        self.preview_btn.clicked.connect(lambda: self.preview_frame())
        btn_row.addWidget(self.preview_btn)

        btn_row.addSpacing(16)
        self.start_btn = QPushButton("开始转换")
        self.start_btn.setMinimumSize(140, 38)
        self.start_btn.setStyleSheet("""
            QPushButton { background: #27ae60; color: white; border: none; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background: #219a52; }
            QPushButton:disabled { background: #bdc3c7; }
        """)
        self.start_btn.clicked.connect(self.start_convert)
        btn_row.addWidget(self.start_btn)

        btn_row.addSpacing(16)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumSize(100, 38)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_convert)
        btn_row.addWidget(self.cancel_btn)

        btn_row.addSpacing(16)
        self.open_dir_btn = QPushButton("打开输出位置")
        self.open_dir_btn.setMinimumSize(120, 38)
        self.open_dir_btn.setEnabled(False)
        self.open_dir_btn.clicked.connect(self.open_output_dir)
        btn_row.addWidget(self.open_dir_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # --- 进度 ---
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #555; font-size: 12px;")
        root.addWidget(self.status_label)
        root.addStretch()

        self._inputs = [self.open_btn, self.radius_combo, self.bright_combo,
                        self.enhance_combo, self.invert_check, self.scale_combo,
                        self.audio_check, self.radio_h264, self.radio_mp4v,
                        self.radio_png, self.frame_slider, self.preview_btn]

    # ------------------------------------------------------- 输入 / 元数据
    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if os.path.splitext(url.toLocalFile())[1].lower() in VIDEO_EXTS:
                event.acceptProposedAction()
                return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.splitext(path)[1].lower() in VIDEO_EXTS:
                self.set_video(path)
                return

    def pick_video(self):
        exts = " ".join("*" + e for e in VIDEO_EXTS)
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "",
            "视频文件 (%s);;所有文件 (*.*)" % exts)
        if path:
            self.set_video(path)

    def set_video(self, path):
        if not os.path.exists(path):
            QMessageBox.warning(self, "提示", "文件不存在：\n%s" % path)
            return
        self.video_path = path
        display = path if len(path) < 46 else "..." + path[-43:]
        self.path_label.setText(display)
        self.path_label.setToolTip(path)
        self.load_meta()

    def load_meta(self):
        cap = cv2.VideoCapture(self.video_path)
        self.meta = None
        if not cap.isOpened():
            cap.release()
            self.info_label.setText("⚠ 无法打开该视频，请检查文件是否损坏")
            self.frame_slider.setRange(0, 0)
            self.frame_slider.setEnabled(False)
            self.frame_label.setText("第 - / - 帧")
            return
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        self.meta = (fps, total, w, h)
        dur = (total / fps) if fps > 0 else 0
        self.info_label.setText(
            "%d × %d · %.2f fps · %d 帧 · 时长约 %s"
            % (w, h, fps, total, _fmt_time(dur)))
        if total > 0:
            self.frame_slider.setRange(0, total - 1)
            self.frame_slider.setEnabled(True)
            self.frame_slider.setValue(0)
            self.frame_label.setText("第 1 / %d 帧" % total)
        else:
            self.frame_slider.setRange(0, 0)
            self.frame_slider.setEnabled(False)
            self.frame_label.setText("第 - / - 帧")

    # ------------------------------------------------------------ 参数
    def _params(self):
        return {
            "min_radius": int(self.radius_combo.currentText()),
            "brightness_offset": int(self.bright_combo.currentText()),
            "enhance_mode": ENHANCE_MAP[self.enhance_combo.currentText()],
            "invert": self.invert_check.isChecked(),
        }

    def _out_mode(self):
        if self.radio_png.isChecked():
            return OUT_PNG
        if self.radio_mp4v.isChecked():
            return OUT_MP4V
        return OUT_H264

    def _refresh_output_state(self):
        """没有 ffmpeg 时禁用 H.264 与音频选项。"""
        has = bool(self.ffmpeg)
        self.radio_h264.setEnabled(has)
        if not has and self.radio_h264.isChecked():
            self.radio_mp4v.setChecked(True)
        self.audio_check.setEnabled(has and self._out_mode() != OUT_PNG)
        if self._out_mode() == OUT_PNG:
            self.audio_check.setChecked(False)

    def _on_slider_changed(self, value):
        total = self.meta[1] if self.meta else 0
        if total > 0:
            self.frame_label.setText("第 %d / %d 帧" % (value + 1, total))
        if self.frame_slider.isEnabled():
            self._preview_timer.start()

    # ------------------------------------------------------------ 预览
    def preview_frame(self):
        if not self.video_path or self.meta is None:
            QMessageBox.warning(self, "提示", "请先选择视频！")
            return
        if self.convert_worker is not None and self.convert_worker.isRunning():
            return
        idx = self.frame_slider.value()
        self._preview_seq += 1
        w = FramePreviewWorker(self.video_path, idx, self._params(), self._preview_seq)
        self._frame_workers.add(w)
        w.frame_ready.connect(self._on_frame_ready)
        w.error.connect(self._on_preview_error)
        w.finished.connect(lambda: self._frame_workers.discard(w))
        w.start()

    def _on_frame_ready(self, seq, arr):
        if seq < self._last_shown_seq:      # 过期结果，丢弃
            return
        self._last_shown_seq = seq
        if self.preview_window is None:
            self.preview_window = PreviewWindow(None)
        self.preview_window.show_image(arr)
        self.preview_window.show()
        self.preview_window.raise_()

    def _on_preview_error(self, msg):
        self.status_label.setText("预览失败：%s" % msg)

    # ------------------------------------------------------------ 转换
    def start_convert(self):
        if not self.video_path or self.meta is None:
            QMessageBox.warning(self, "提示", "请先选择视频！")
            return

        mode = self._out_mode()
        if mode == OUT_H264 and not self.ffmpeg:
            self.radio_mp4v.setChecked(True)
            mode = OUT_MP4V
            QMessageBox.information(self, "提示", "没有找到 ffmpeg，已改用 OpenCV 内置编码。")

        stem = os.path.splitext(os.path.basename(self.video_path))[0]
        if mode == OUT_PNG:
            folder = QFileDialog.getExistingDirectory(
                self, "选择保存帧序列的文件夹", "")
            if not folder:
                return
            if os.listdir(folder):
                ret = QMessageBox.question(
                    self, "提示",
                    "该文件夹不为空，继续写入可能覆盖同名文件。\n是否继续？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if ret != QMessageBox.Yes:
                    return
            out_path = folder
        else:
            default = os.path.join(os.path.dirname(self.video_path),
                                   stem + "_线稿.mp4")
            out_path, _ = QFileDialog.getSaveFileName(
                self, "保存线稿视频", default, "MP4 视频 (*.mp4)")
            if not out_path:
                return
            if not out_path.lower().endswith(".mp4"):
                out_path += ".mp4"

        scale = self.scale_combo.currentData()
        keep_audio = self.audio_check.isChecked() and mode != OUT_PNG
        tmp_path = ""
        if mode != OUT_PNG:
            tmp_path = out_path + ".lineart.tmp.mp4"

        self.convert_worker = ConvertWorker(
            self.video_path, out_path, mode, self._params(), scale,
            keep_audio, self.ffmpeg)
        self.convert_worker.tmp_path = tmp_path
        self.convert_worker.progress.connect(self._on_progress)
        self.convert_worker.sampled.connect(self._on_sampled)
        self.convert_worker.status.connect(lambda s: self.status_label.setText(s))
        self.convert_worker.finished_ok.connect(self._on_convert_done)
        self.convert_worker.cancelled.connect(self._on_convert_cancelled)
        self.convert_worker.error.connect(self._on_convert_error)

        self._set_running(True)
        self._t0 = time.time()
        self.progress.setRange(0, 100 if not self.meta[1] else self.meta[1])
        self.progress.setValue(0)
        self.status_label.setText("开始转换...")
        self.convert_worker.start()

    def cancel_convert(self):
        if self.convert_worker is not None and self.convert_worker.isRunning():
            self.convert_worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status_label.setText("正在取消...")

    def _set_running(self, running):
        for w in self._inputs:
            w.setEnabled(not running)
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        if not running:
            self._refresh_output_state()

    def _on_progress(self, done, total):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(min(done, total))
            self.progress.setFormat("%d / %d 帧（%d%%）"
                                    % (done, total, done * 100 // max(1, total)))
        else:
            self.progress.setRange(0, 0)
        elapsed = time.time() - self._t0
        if done > 0 and elapsed > 0:
            speed = done / elapsed
            left = (total - done) / speed if total > 0 else 0
            self.status_label.setText(
                "已处理 %d 帧 · %.1f 帧/秒 · 已用 %s · 预计剩余 %s"
                % (done, speed, _fmt_time(elapsed), _fmt_time(left)))

    def _on_sampled(self, arr):
        if self.preview_window is not None and self.preview_window.isVisible():
            self.preview_window.show_image(arr)

    def _on_convert_done(self, out_path):
        self._set_running(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress.setFormat("完成")
        self.out_path = out_path
        self.open_dir_btn.setEnabled(True)
        if self._out_mode() == OUT_PNG:
            n = len([f for f in os.listdir(out_path) if f.lower().endswith(".png")]) \
                if os.path.isdir(out_path) else 0
            self.status_label.setText("完成：已输出 %d 张 PNG 到 %s" % (n, out_path))
        else:
            size = os.path.getsize(out_path) / 1024 / 1024 if os.path.exists(out_path) else 0
            self.status_label.setText("完成：%s（%.1f MB）" % (out_path, size))
        QMessageBox.information(self, "完成", "线稿已输出到：\n%s" % out_path)

    def _on_convert_cancelled(self):
        self._set_running(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("已取消")
        self.status_label.setText("已取消（未完成的输出文件已删除）")

    def _on_convert_error(self, msg):
        self._set_running(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("失败")
        self.status_label.setText("失败：%s" % msg)
        QMessageBox.critical(self, "错误", msg)

    def open_output_dir(self):
        if not self.out_path:
            return
        folder = self.out_path if os.path.isdir(self.out_path) else os.path.dirname(self.out_path)
        try:
            if hasattr(os, "startfile"):
                os.startfile(folder)          # Windows
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(self, "提示", "打开文件夹失败：%s" % e)

    def closeEvent(self, event):
        if self.convert_worker is not None and self.convert_worker.isRunning():
            ret = QMessageBox.question(
                self, "提示", "正在转换中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret != QMessageBox.Yes:
                event.ignore()
                return
            self.convert_worker.cancel()
            self.convert_worker.wait(3000)
        event.accept()


def load_video_line_art():
    """工具菜单入口：单独起一个进程打开窗口，避免拖慢主界面。"""
    import multiprocessing
    p = multiprocessing.Process(target=run_video_line_art)
    p.start()


def run_video_line_art():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))

    from PyQt5.QtGui import QIcon
    for icon_path in ("./工具/LineArt/app_icon.png", "app_icon.png"):
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

    app.setStyleSheet("""
        QMainWindow { background: #ffffff; }
        QGroupBox { font-weight: bold; border: 1px solid #ddd; border-radius: 6px; margin-top: 10px; padding-top: 14px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        QComboBox { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; min-width: 90px; }
        QComboBox:hover { border-color: #3498db; }
        QLabel { font-size: 13px; }
        QProgressBar { border: 1px solid #ddd; border-radius: 4px; text-align: center; height: 20px; }
        QProgressBar::chunk { background: #27ae60; border-radius: 3px; }
    """)

    window = VideoLineArtGUI()
    window.move(300, 250)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_video_line_art()
