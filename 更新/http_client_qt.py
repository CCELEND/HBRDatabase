import json
import os
import requests
import threading
from urllib.parse import quote
from PyQt5.QtWidgets import (QDialog, QProgressBar, QLabel, QVBoxLayout,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon

from tools import (creat_directory, confirm_restart_qt, sort_dict_by_key,
                   safe_relative_path)
from 更新.hash import save_hashes_to_json
from 更新.server_config import requests_kwargs as _tls_kwargs
from 日志.advanced_logger import AdvancedLogger

logger = AdvancedLogger.get_logger(__name__)

_is_updating = False
_update_lock = threading.Lock()

def is_updating():
    with _update_lock:
        return _is_updating

def set_updating(val):
    with _update_lock:
        global _is_updating
        _is_updating = val

# ---------- 信号类，用于跨线程更新 UI ----------
class DownloadSignals(QObject):
    progress = pyqtSignal(int, int)          # (current_file_progress, overall_percent)
    file_status = pyqtSignal(str)            # 当前正在下载的文件名
    status_message = pyqtSignal(str)         # 状态文字
    finished = pyqtSignal()                  # 下载完成
    error = pyqtSignal(str)                  # 错误消息
    cancelled = pyqtSignal()                 # 用户取消

# 关闭对话框时线程可能还没退出：持有引用，等它自己结束，
# 否则 QThread 在运行中被 Python 回收会直接崩溃。
_LIVE_THREADS = set()

def _keep_thread(thread):
    _LIVE_THREADS.add(thread)
    thread.finished.connect(lambda: _LIVE_THREADS.discard(thread))


class _DownloadCancelled(Exception):
    """用户取消下载。"""

# ---------- 下载线程 ----------
class DownloadThread(QThread):
    def __init__(self, server_url, files_to_download, server_file_hashes):
        super().__init__()
        self.server_url = server_url
        self.files_to_download = files_to_download
        self.server_file_hashes = server_file_hashes
        self.signals = DownloadSignals()
        self._cancel = threading.Event()
        self._response = None
        self._current_path = None

    def cancel(self):
        """协作式取消：不再调用 QThread.terminate()。"""
        self._cancel.set()
        response = self._response
        if response is not None:
            try:
                response.close()   # 打断正在阻塞的 iter_content()
            except Exception:
                pass

    def _remove_current(self):
        if self._current_path:
            try:
                if os.path.exists(self._current_path):
                    os.remove(self._current_path)
            except OSError:
                pass
            self._current_path = None

    def run(self):
        total = len(self.files_to_download)
        for i, file_name in enumerate(self.files_to_download):
            if self._cancel.is_set():
                self._remove_current()
                self.signals.cancelled.emit()
                return
            try:
                self.signals.file_status.emit(f"下载更新：'{file_name}' ({i+1}/{total})")
                # 服务器给的路径只允许落在程序目录内
                safe_path = safe_relative_path(file_name)
                creat_directory(file_name)
                self._current_path = safe_path

                encoded_name = quote(file_name)
                url = f"{self.server_url}/download/{encoded_name}"
                with requests.get(url, stream=True, timeout=30,
                                  **_tls_kwargs()) as response:
                    self._response = response
                    try:
                        response.raise_for_status()
                        if response.status_code != 200:
                            err_info = response.json()
                            error_msg = err_info.get('error', '未知错误')
                            self.signals.error.emit(error_msg)
                            return

                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        with open(safe_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if self._cancel.is_set():
                                    raise _DownloadCancelled()
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        file_progress = int(downloaded / total_size * 100)
                                        overall = i * 100 + file_progress
                                        self.signals.progress.emit(file_progress, int(overall / total))
                    finally:
                        self._response = None
                # 完成一个文件，更新整体进度
                self._current_path = None
                overall = (i + 1) * 100 // total
                self.signals.progress.emit(100, overall)  # 文件100% 整体进度
            except _DownloadCancelled:
                self._remove_current()
                self.signals.cancelled.emit()
                return
            except Exception as e:
                self._remove_current()
                if self._cancel.is_set():
                    self.signals.cancelled.emit()
                else:
                    error_msg = f"'{file_name}' 下载失败\n{str(e)}"
                    self.signals.error.emit(error_msg)
                return

        if self._cancel.is_set():
            self.signals.cancelled.emit()
            return

        # 下载完成，保存服务端哈希
        if self.server_file_hashes:
            sorted_hashes = sort_dict_by_key(self.server_file_hashes)
            save_hashes_to_json(sorted_hashes, "./关于/server_file_hashes.json")
        self.signals.finished.emit()


# ---------- 进度对话框 ----------
class UpdateProgressDialog(QDialog):
    def __init__(self, parent, server_url, files_to_download, server_file_hashes):
        super().__init__(parent)
        self.setWindowTitle("更新")
        self.resize(600, 180)
        self.setWindowIcon(QIcon("./更新/net.png"))  # 假设存在
        self.setModal(True)

        layout = QVBoxLayout(self)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("正在下载更新资源...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.percent_label)

        self.file_label = QLabel("")
        self.file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.file_label)

        self._closing = False

        # 启动下载线程
        self.download_thread = DownloadThread(server_url, files_to_download, server_file_hashes)
        _keep_thread(self.download_thread)
        # 无论正常结束还是取消，线程真正退出后再解锁更新状态
        self.download_thread.finished.connect(lambda: set_updating(False))
        # 连接信号
        self.download_thread.signals.progress.connect(self.update_progress)
        self.download_thread.signals.file_status.connect(self.file_label.setText)
        self.download_thread.signals.status_message.connect(self.status_label.setText)
        self.download_thread.signals.finished.connect(self.on_finished)
        self.download_thread.signals.error.connect(self.on_error)
        self.download_thread.signals.cancelled.connect(self.on_cancelled)

        self.download_thread.start()

    def update_progress(self, file_progress, overall_percent):
        self.progress_bar.setValue(overall_percent)
        self.percent_label.setText(f"{overall_percent}%")

    def on_finished(self):
        if self._closing:
            return
        self._closing = True
        self.status_label.setText("更新完成！")
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        # 询问重启
        confirm_restart_qt("更新完成")
        self.close()

    def on_error(self, error_msg):
        if self._closing:
            return
        self._closing = True
        self.status_label.setText("下载出错")
        QMessageBox.critical(self, "错误", error_msg)
        self.close()

    def on_cancelled(self):
        if self._closing:
            return
        self._closing = True
        self.status_label.setText("已取消")
        self.close()

    def closeEvent(self, event):
        # 正常结束/出错时由对应槽主动关闭，不再重复取消
        if self._closing:
            event.accept()
            return

        if self.download_thread.isRunning():
            ret = QMessageBox.question(
                self, "提示", "正在下载更新，确定要取消并退出吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret != QMessageBox.Yes:
                event.ignore()
                return

            self._closing = True
            self.download_thread.cancel()
            # 协作取消后通常很快退出；超时也放行，线程对象由 _LIVE_THREADS 持有
            if not self.download_thread.wait(3000):
                logger.warning("更新下载线程未在 3 秒内退出，将在后台继续收尾")

        self._closing = True
        event.accept()


# ---------- 对外接口 ----------
def send_hashes_to_server(server_url, client_file_hashes, oper="update", sys="windows"):
    headers = {'Content-Type': 'application/json'}
    payload = {"ver": "PyQT5", "oper": oper, "sys": sys, "hashes": client_file_hashes}
    response = requests.post(server_url, data=json.dumps(payload), headers=headers,
                             timeout=5, **_tls_kwargs())
    return response.json()


def download_files_from_server(parent, server_url, files_to_download, server_file_hashes):
    if is_updating():
        return
    if files_to_download:
        set_updating(True)
        dialog = UpdateProgressDialog(parent, server_url, files_to_download, server_file_hashes)
        dialog.exec_()
        # 线程正常结束时 finished 信号会解锁；用户取消时若线程还在收尾，
        # 保持 updating=True，等线程真正退出后再解锁。
        if not dialog.download_thread.isRunning():
            set_updating(False)
    else:
        QMessageBox.information(parent, "提示", "已是最新版本")