import json
import requests
import threading
from urllib.parse import quote
from PyQt5.QtWidgets import (QDialog, QProgressBar, QLabel, QVBoxLayout,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon

from tools import creat_directory, confirm_restart_qt, sort_dict_by_key
from 更新.hash import save_hashes_to_json
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

# ---------- 下载线程 ----------
class DownloadThread(QThread):
    def __init__(self, server_url, files_to_download, server_file_hashes):
        super().__init__()
        self.server_url = server_url
        self.files_to_download = files_to_download
        self.server_file_hashes = server_file_hashes
        self.signals = DownloadSignals()

    def run(self):
        total = len(self.files_to_download)
        for i, file_name in enumerate(self.files_to_download):
            try:
                self.signals.file_status.emit(f"下载更新：'{file_name}' ({i+1}/{total})")
                creat_directory(file_name)

                encoded_name = quote(file_name)
                url = f"{self.server_url}/download/{encoded_name}"
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    if response.status_code != 200:
                        err_info = response.json()
                        error_msg = err_info.get('error', '未知错误')
                        self.signals.error.emit(error_msg)
                        return

                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    with open(file_name, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    file_progress = int(downloaded / total_size * 100)
                                    overall = i * 100 + file_progress
                                    self.signals.progress.emit(file_progress, int(overall / total))
                                    # 发送整体百分比 (0-100)
                                    # 但为了更好控制，可以用两个参数：文件进度和整体进度
                                    # 这里只发送整体百分比
                # 完成一个文件，更新整体进度
                overall = (i + 1) * 100 // total
                self.signals.progress.emit(100, overall)  # 文件100% 整体进度
            except Exception as e:
                error_msg = f"'{file_name}' 下载失败\n{str(e)}"
                self.signals.error.emit(error_msg)
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
        self.setWindowIcon(QIcon("./更新/net.ico"))  # 假设存在
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

        # 启动下载线程
        self.download_thread = DownloadThread(server_url, files_to_download, server_file_hashes)
        # 连接信号
        self.download_thread.signals.progress.connect(self.update_progress)
        self.download_thread.signals.file_status.connect(self.file_label.setText)
        self.download_thread.signals.status_message.connect(self.status_label.setText)
        self.download_thread.signals.finished.connect(self.on_finished)
        self.download_thread.signals.error.connect(self.on_error)

        self.download_thread.start()

    def update_progress(self, file_progress, overall_percent):
        self.progress_bar.setValue(overall_percent)
        self.percent_label.setText(f"{overall_percent}%")

    def on_finished(self):
        self.status_label.setText("更新完成！")
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        # 询问重启
        confirm_restart_qt("更新完成")
        self.close()

    def on_error(self, error_msg):
        self.status_label.setText("下载出错")
        QMessageBox.critical(self, "错误", error_msg)
        self.close()

    def closeEvent(self, event):
        # 强制停止线程？最好等待线程结束，但这里简单处理
        if self.download_thread.isRunning():
            self.download_thread.terminate()  # 不推荐，但简单
        event.accept()


# ---------- 对外接口 ----------
def send_hashes_to_server(server_url, client_file_hashes):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(client_file_hashes), headers=headers, timeout=5)
    return response.json()


def download_files_from_server(parent, server_url, files_to_download, server_file_hashes):
    if is_updating():
        return
    if files_to_download:
        set_updating(True)
        dialog = UpdateProgressDialog(parent, server_url, files_to_download, server_file_hashes)
        # 对话框结束后释放锁，但需要在对话框关闭时设置
        # 利用 finished 或 closeEvent 来重置
        # 我们在 UpdateProgressDialog 的 finish/error 处重置
        dialog.exec_()
        # 注意：dialog.exec_() 会阻塞直到关闭，但下载线程在后台运行，关闭时线程可能还在运行
        # 更好的做法是使用非模态对话框，但这里为简单保持模态
        set_updating(False)  # 但可能在线程未完成时就被重置，需要更精细控制
    else:
        QMessageBox.information(parent, "提示", "已是最新版本")

# 修正 UpdateProgressDialog 的关闭重置
# 修改 on_finished 和 on_error 中调用 set_updating(False)