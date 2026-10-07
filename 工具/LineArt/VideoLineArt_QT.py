# -*- coding: utf-8 -*-
# pip install PyQt5 opencv-python numpy
"""视频转线稿工具。

把整段视频逐帧转成线稿，输出：

* MP4 线稿视频（H.264，可保留原视频音频；需要系统里有 ffmpeg）
* MP4 线稿视频（OpenCV 内置编码，无需 ffmpeg）
* PNG 帧序列（存到一个文件夹里）

线稿算法与「图片转线稿工具 2.0」完全一致，见 :mod:`工具.LineArt.line_art_core`。
"""
import gzip
import json
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
    QPushButton, QRadioButton, QSlider, QStatusBar, QStyle, QStyleOptionSlider,
    QVBoxLayout, QWidget
)

from 工具.LineArt.line_art_core import ENHANCE_MAP, VIDEO_EXTS, to_line_art
from 工具.LineArt.LineArtGUI2_QT import ImageViewer

# 让 ffmpeg 子进程不弹出黑色控制台窗口（Windows）
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# ---------------------------------------------------------------------------
# 项目自带的 ffmpeg（工具/LineArt/ffmpeg/）
#
# 原版 ffmpeg.exe 有一百多 MB，直接放进分发包太重，所以压成 ffmpeg.exe.gz
# 随项目分发；第一次用到时解压到 %LOCALAPPDATA%\HBRDatabase\ffmpeg\ 并复用。
# 解压目标故意不放在项目目录里：那里的文件会被哈希/更新逻辑当成待分发内容。
# 项目换了 ffmpeg 版本后，靠 ffmpeg_info.json 里的 exe_sha256 让旧缓存作废重解压。
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(_HERE, "ffmpeg")
BUNDLED_FFMPEG = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
BUNDLED_FFMPEG_GZ = os.path.join(FFMPEG_DIR, "ffmpeg.exe.gz")
FFMPEG_INFO = os.path.join(FFMPEG_DIR, "ffmpeg_info.json")


def ffmpeg_cache_path() -> str:
    """解压出来的 ffmpeg 存放位置。"""
    base = (os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP")
            or tempfile.gettempdir())
    return os.path.join(base, "HBRDatabase", "ffmpeg", "ffmpeg.exe")


def _bundled_info() -> dict:
    """读项目自带的 ffmpeg_info.json（版本 / 大小 / 校验值）。"""
    try:
        with open(FFMPEG_INFO, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _min_ffmpeg_size() -> int:
    """缓存文件至少要有这么大才算完整（优先用 ffmpeg_info.json 里的原始大小）。"""
    size = int(_bundled_info().get("raw_size") or 0)
    return size if size > 0 else 50 * 1024 * 1024


def bundled_ffmpeg_available() -> bool:
    """项目里带没带 ffmpeg（原版 exe 或压缩包）。"""
    return os.path.exists(BUNDLED_FFMPEG) or os.path.exists(BUNDLED_FFMPEG_GZ)


# 输出方式
OUT_H264 = "h264"    # ffmpeg 编码 H.264，画质好、体积小，可带音频
OUT_MP4V = "mp4v"    # OpenCV 内置编码，任何环境都能用，无音频
OUT_PNG = "png"      # PNG 帧序列


def _cache_is_current(cache: str) -> bool:
    """本地缓存是不是「和项目自带的那个版本一致」。

    项目换了 ffmpeg 版本后，旧缓存必须作废重新解压，否则用户会一直用旧的。
    """
    if not os.path.exists(cache) or os.path.getsize(cache) < _min_ffmpeg_size():
        return False
    expected = str(_bundled_info().get("exe_sha256") or "")
    if not expected:
        return True            # 没有版本信息（比如有人手工放了原版 exe）
    try:
        with open(cache + ".json", encoding="utf-8") as f:
            marker = json.load(f)
    except Exception:
        return False
    return marker.get("exe_sha256") == expected


def find_ffmpeg() -> str:
    """找一个可用的 ffmpeg（不会解压，立刻返回）。

    优先级：项目自带的原版 exe > 版本匹配的本地缓存 > 系统 PATH。
    """
    if os.path.exists(BUNDLED_FFMPEG):
        return BUNDLED_FFMPEG
    cache = ffmpeg_cache_path()
    if _cache_is_current(cache):
        return cache
    return shutil.which("ffmpeg") or ""


def ensure_ffmpeg() -> str:
    """确保有 ffmpeg 可用，而且版本和项目自带的一致。

    项目自带的是压缩包，需要时解压到本地缓存；项目换了版本会重新解压。
    """
    if os.path.exists(BUNDLED_FFMPEG):
        return BUNDLED_FFMPEG
    cache = ffmpeg_cache_path()
    if _cache_is_current(cache):
        return cache
    if not os.path.exists(BUNDLED_FFMPEG_GZ):
        return find_ffmpeg()          # 没带压缩包，退回系统 PATH
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    tmp = cache + ".part"
    # 先解压到 .part 再改名，避免中途失败留下半个文件被当成可用
    with gzip.open(BUNDLED_FFMPEG_GZ, "rb") as fin:
        with open(tmp, "wb") as fout:
            shutil.copyfileobj(fin, fout, 1024 * 1024)
    os.replace(tmp, cache)
    # 记下版本，下次靠它判断缓存还有没有效
    try:
        with open(cache + ".json", "w", encoding="utf-8") as f:
            json.dump(_bundled_info(), f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return cache if os.path.exists(cache) else ""


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


# ---------------------------------------------------------------------------
# 编码器（GPU 加速就靠这里）
#
# 实测结论（RTX 2060 + 1080p）：
#   * 硬件编码（NVENC）把编码丢给显卡，CPU 全部留给解码和线稿 -> 整体约 2 倍速；
#   * 硬件解码（NVDEC）反而更慢，不用；
#   * 线稿算法走 OpenCL(GPU) 也比 CPU 慢，不用（CPU 的 erode 已经是可分离+多线程）。
# ---------------------------------------------------------------------------

HW_ENCODERS = ("h264_nvenc", "h264_qsv", "h264_amf")

# 界面上「编码器」下拉框的选项：(内部名, 显示文字)
ENCODER_CHOICES = [
    ("auto", "自动（有 GPU 就用 GPU）"),
    ("h264_nvenc", "NVIDIA NVENC（GPU）"),
    ("h264_qsv", "Intel QSV（GPU）"),
    ("h264_amf", "AMD AMF（GPU）"),
    ("libx264", "CPU x264 高画质"),
    ("libx264_fast", "CPU x264 快速"),
]

_ENCODER_PROBE_CACHE = {}

# 编码器内部名 -> 显示名（状态栏用）
ENCODER_LABELS = {
    "h264_nvenc": "NVIDIA NVENC（GPU）",
    "h264_qsv": "Intel QSV（GPU）",
    "h264_amf": "AMD AMF（GPU）",
    "libx264": "CPU x264 高画质",
    "libx264_fast": "CPU x264 快速",
}


def build_encode_cmd(ffmpeg: str, encoder: str, out_path: str,
                     width: int, height: int, fps: float) -> list:
    """生成把灰度原始帧编码成 H.264 的 ffmpeg 命令（帧从 stdin 喂进去）。"""
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "gray",
           "-s", "%dx%d" % (width, height),
           "-r", "%.6f" % fps, "-i", "-"]
    if encoder == "h264_nvenc":       # NVIDIA 显卡
        cmd += ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr",
                "-cq", "19", "-pix_fmt", "yuv420p"]
    elif encoder == "h264_qsv":       # Intel 核显
        cmd += ["-c:v", "h264_qsv", "-preset", "medium",
                "-global_quality", "19", "-pix_fmt", "nv12"]
    elif encoder == "h264_amf":       # AMD 显卡
        cmd += ["-c:v", "h264_amf", "-quality", "balanced", "-rc", "cqp",
                "-qp_i", "20", "-qp_p", "20", "-pix_fmt", "yuv420p"]
    elif encoder == "libx264_fast":
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p"]
    else:                             # libx264 高画质
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p"]
    cmd += [out_path]
    return cmd


def list_ffmpeg_encoders(ffmpeg: str) -> set:
    """ffmpeg 编译里带哪些硬件编码器（只看列表，很快）。"""
    if not ffmpeg:
        return set()
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-encoders"],
                           capture_output=True, creationflags=_NO_WINDOW,
                           timeout=30)
        text = r.stdout.decode("utf-8", "replace")
        return {name for name in HW_ENCODERS if (" %s " % name) in text}
    except Exception:
        return set()


def probe_encoder(ffmpeg: str, encoder: str) -> bool:
    """真的试编一帧，确认这台机器上这个编码器能用（结果会缓存）。"""
    if encoder not in HW_ENCODERS:
        return bool(ffmpeg)
    if not ffmpeg:
        return False
    if encoder in _ENCODER_PROBE_CACHE:
        return _ENCODER_PROBE_CACHE[encoder]
    ok = False
    out = ""
    try:
        fd, out = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        cmd = build_encode_cmd(ffmpeg, encoder, out, 320, 240, 25.0)
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             creationflags=_NO_WINDOW)
        p.stdin.write(b"\x80" * (320 * 240))
        p.stdin.close()
        p.wait(timeout=60)
        ok = (p.returncode == 0 and os.path.exists(out)
              and os.path.getsize(out) > 0)
    except Exception:
        ok = False
    finally:
        try:
            if out and os.path.exists(out):
                os.remove(out)
        except OSError:
            pass
    _ENCODER_PROBE_CACHE[encoder] = ok
    return ok


# 持有运行中的 QThread 引用：窗口先关掉时，线程对象不能被 Python 回收，
# 否则 Qt 会报 "QThread: Destroyed while thread is still running" 甚至崩溃。
_LIVE_WORKERS = set()


def _keep_worker(worker):
    _LIVE_WORKERS.add(worker)
    worker.finished.connect(lambda: _LIVE_WORKERS.discard(worker))


class FfmpegPrepareWorker(QThread):
    """后台准备 ffmpeg：需要的话先解压自带压缩包，再试编确认哪些 GPU 编码器真能用。"""

    done = pyqtSignal(str, dict, str)      # (ffmpeg 路径, {编码器: 可用}, 错误信息)

    def __init__(self, ffmpeg):
        super().__init__()
        self.ffmpeg = ffmpeg

    def run(self):
        ff = self.ffmpeg
        error = ""
        if not ff:
            try:
                ff = ensure_ffmpeg()
            except Exception as e:
                ff, error = "", "解压 ffmpeg 失败：%s" % e
        usable = {}
        if ff:
            try:
                for enc in list_ffmpeg_encoders(ff):
                    usable[enc] = probe_encoder(ff, enc)
            except Exception as e:
                error = error or str(e)
        self.done.emit(ff, usable, error)


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
                 keep_audio, ffmpeg, encoder="libx264"):
        super().__init__()
        self.video_path = video_path
        self.out_path = out_path
        self.out_mode = out_mode
        self.params = params
        self.scale = scale
        self.keep_audio = keep_audio
        self.ffmpeg = ffmpeg
        self.encoder = encoder
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
                cmd = build_encode_cmd(self.ffmpeg, self.encoder, self.tmp_path,
                                       out_w, out_h, fps)
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


class JumpSlider(QSlider):
    """点滑槽任意位置直接跳到那里（原生 QSlider 点击只翻一页）。

    点住滑槽不放还能继续拖，行为和其他播放器一致。
    """

    def _value_at(self, pos):
        """把鼠标坐标换算成滑块值。"""
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        handle = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        if self.orientation() == Qt.Horizontal:
            span = groove.width() - handle.width()
            offset = pos.x() - groove.x() - handle.width() // 2
        else:
            span = groove.height() - handle.height()
            offset = pos.y() - groove.y() - handle.height() // 2
        if span <= 0:
            return self.value()
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), offset, span)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            handle = self.style().subControlRect(
                QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            if not handle.contains(event.pos()):
                # 点在滑槽上：直接跳过去，并记下状态以便继续拖
                self._jumping = True
                self.setValue(self._value_at(event.pos()))
                event.accept()
                return
        self._jumping = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_jumping", False):
            self.setValue(self._value_at(event.pos()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, "_jumping", False):
            self._jumping = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


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
        self.hw_encoders = list_ffmpeg_encoders(self.ffmpeg)
        self.hw_usable = None       # 后台试编结果，None 表示还在检测
        # 打开窗口时就要知道「等会儿能不能用上 ffmpeg」，否则界面会先闪一下"未找到"
        self._preparing = bool(self.ffmpeg) or bundled_ffmpeg_available()
        self._prepare_error = ""
        self._probe_worker = None
        self.preview_window = None
        self._frame_workers = set()
        self._preview_seq = 0
        self._last_shown_seq = -1
        self.convert_worker = None
        self.out_path = ""
        self._t0 = 0.0

        self._init_ui()
        self._refresh_output_state()
        self._start_ffmpeg_prepare()

    def _start_ffmpeg_prepare(self):
        """后台准备 ffmpeg（必要时解压）+ 检测 GPU 编码器。"""
        if not self._preparing:
            return
        self._probe_worker = FfmpegPrepareWorker(self.ffmpeg)
        self._probe_worker.done.connect(self._on_ffmpeg_prepare_done)
        _keep_worker(self._probe_worker)
        self._probe_worker.start()

    def _on_ffmpeg_prepare_done(self, ffmpeg, usable, error):
        self._preparing = False
        self._prepare_error = error
        if ffmpeg:
            self.ffmpeg = ffmpeg
            self.hw_encoders = set(usable) or list_ffmpeg_encoders(ffmpeg)
        self.hw_usable = usable
        self._rebuild_encoder_combo(usable)
        self.gpu_label.setText(self._encoder_hint())
        self.gpu_label.setToolTip(
            "ffmpeg：%s\n版本：%s"
            % (self.ffmpeg or "(未找到)", _bundled_info().get("version", "?")))
        self._refresh_output_state()

    def _rebuild_encoder_combo(self, usable):
        """按「真的能用」的结果重建编码器下拉框（保留用户当前的选择）。"""
        keep = self.encoder_combo.currentData()
        self.encoder_combo.blockSignals(True)
        self.encoder_combo.clear()
        for name, text in ENCODER_CHOICES:
            if name in HW_ENCODERS and not usable.get(name):
                continue
            self.encoder_combo.addItem(text, name)
        idx = self.encoder_combo.findData(keep)
        self.encoder_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.encoder_combo.blockSignals(False)

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
        opt_row.addSpacing(16)
        opt_row.addWidget(QLabel("编码器："))
        self.encoder_combo = QComboBox()
        for name, text in ENCODER_CHOICES:
            if name in HW_ENCODERS and name not in self.hw_encoders:
                continue          # 本机没有的硬件编码器就不列出来
            self.encoder_combo.addItem(text, name)
        opt_row.addWidget(self.encoder_combo)
        self.audio_check = QCheckBox("保留原视频音频（需要 ffmpeg）")
        opt_row.addSpacing(16)
        opt_row.addWidget(self.audio_check)
        opt_row.addStretch()
        out_box.addLayout(opt_row)

        self.gpu_label = QLabel(self._encoder_hint())
        self.gpu_label.setStyleSheet("color: #888; font-size: 12px;")
        out_box.addWidget(self.gpu_label)
        root.addWidget(out_group)

        # --- 预览帧 ---
        prev_row = QHBoxLayout()
        prev_row.addWidget(QLabel("预览帧："))
        self.frame_slider = JumpSlider(Qt.Horizontal)
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
                        self.encoder_combo, self.audio_check, self.radio_h264,
                        self.radio_mp4v, self.radio_png, self.frame_slider,
                        self.preview_btn]

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

    def _encoder_hint(self):
        """底部那行小字：本机 GPU 编码器情况。"""
        if self._preparing:
            if self.ffmpeg:
                return "正在检测 GPU 编码器..."
            return "正在准备 ffmpeg（项目自带，首次使用需解压约 45MB，请稍候）..."
        if not self.ffmpeg:
            if self._prepare_error:
                return "准备 ffmpeg 失败：%s（只能用「内置编码」）" % self._prepare_error
            return "未找到 ffmpeg：只能用「内置编码」，没有 GPU 加速，也不能保留音频。"
        names = {"h264_nvenc": "NVIDIA NVENC", "h264_qsv": "Intel QSV",
                 "h264_amf": "AMD AMF"}
        if self.hw_usable is None:
            return "正在检测 GPU 编码器..."
        parts = []
        for n in HW_ENCODERS:
            if n not in self.hw_encoders:
                continue
            parts.append("%s %s" % (names[n], "✅" if self.hw_usable.get(n) else "❌"))
        if not parts:
            return "没有发现可用的 GPU 编码器，将使用 CPU 编码。"
        return "本机 GPU 编码器：" + "   ".join(parts) + "（「自动」会优先使用 GPU）"

    def _ffmpeg_ready(self):
        """ffmpeg 现在能用，或者正在后台准备（准备完就能用）。"""
        return bool(self.ffmpeg) or self._preparing

    def _resolve_encoder(self):
        """把下拉框选择变成实际要用的编码器；GPU 不可用时自动降级到 CPU。"""
        sel = self.encoder_combo.currentData() or "auto"
        if not self.ffmpeg:
            return "libx264"
        if sel == "auto":
            for enc in HW_ENCODERS:
                if enc in self.hw_encoders and probe_encoder(self.ffmpeg, enc):
                    return enc
            return "libx264_fast"
        if sel in HW_ENCODERS and not probe_encoder(self.ffmpeg, sel):
            QMessageBox.information(
                self, "提示",
                "本机无法使用 %s，已改用 CPU 编码。"
                % dict(ENCODER_CHOICES).get(sel, sel))
            return "libx264_fast"
        return sel

    def _refresh_output_state(self):
        """没有 ffmpeg 时禁用 H.264 与音频选项；编码器只在 H.264 模式下有意义。"""
        has = self._ffmpeg_ready()
        self.radio_h264.setEnabled(has)
        if not has and self.radio_h264.isChecked():
            self.radio_mp4v.setChecked(True)
        is_png = self._out_mode() == OUT_PNG
        self.audio_check.setEnabled(has and not is_png)
        if is_png:
            self.audio_check.setChecked(False)
        self.encoder_combo.setEnabled(has and self._out_mode() == OUT_H264)

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
        _keep_worker(w)
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
            if self._preparing:
                QMessageBox.information(
                    self, "提示",
                    "ffmpeg 正在准备中（首次使用需要解压一次），请等几秒再试。")
                return
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

        encoder = "libx264"
        if mode == OUT_H264:
            self.status_label.setText("正在检测可用编码器...")
            QApplication.processEvents()
            encoder = self._resolve_encoder()

        self.convert_worker = ConvertWorker(
            self.video_path, out_path, mode, self._params(), scale,
            keep_audio, self.ffmpeg, encoder)
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
        if mode == OUT_H264:
            self.status_label.setText("开始转换（编码器：%s）..."
                                      % ENCODER_LABELS.get(encoder, encoder))
        else:
            self.status_label.setText("开始转换...")
        _keep_worker(self.convert_worker)
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
        worker = self.convert_worker
        if worker is not None and worker.out_mode == OUT_PNG:
            n = len([f for f in os.listdir(out_path) if f.lower().endswith(".png")]) \
                if os.path.isdir(out_path) else 0
            self.status_label.setText("完成：已输出 %d 张 PNG 到 %s" % (n, out_path))
        else:
            size = os.path.getsize(out_path) / 1024 / 1024 if os.path.exists(out_path) else 0
            enc = ENCODER_LABELS.get(getattr(worker, "encoder", ""), "")
            self.status_label.setText(
                "完成：%s（%.1f MB%s）"
                % (out_path, size, "，编码器 " + enc if enc else ""))
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
