from 更新.hash import calculate_file_hashes
from 更新.http_client_qt import send_hashes_to_server, download_files_from_server
from 更新.server_config import server_url as get_server_url
import 更新.http_client_qt as http_client_qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from 日志.advanced_logger import AdvancedLogger
from tools import get_os_info

logger = AdvancedLogger.get_logger(__name__)

# 持有 worker 引用，避免 QThread 被 GC
_ACTIVE_WORKERS = []


class _UpdateCheckWorker(QThread):
    """后台计算哈希并请求服务器，避免卡死 UI 线程。"""

    done = pyqtSignal(object, object)  # (response, error)

    def run(self):
        try:
            current_file_hashes = calculate_file_hashes("./")
            server_url = get_server_url()
            sys_info = get_os_info()
            response = send_hashes_to_server(
                server_url, current_file_hashes, "update", sys_info)
            self.done.emit(response, None)
        except Exception as e:
            self.done.emit(None, e)


def http_update_data(parent_widget):
    if http_client_qt.is_updating():
        return

    worker = _UpdateCheckWorker()
    _ACTIVE_WORKERS.append(worker)

    def on_done(response, error):
        try:
            if worker in _ACTIVE_WORKERS:
                _ACTIVE_WORKERS.remove(worker)
            if error is not None:
                logger.error(f"连接失败：{str(error)}\n请重试或联系开发者")
                QMessageBox.critical(
                    parent_widget, "错误",
                    f"连接失败：{str(error)}\n请重试或联系开发者")
                return
            if response and 'files_to_download' in response:
                http_client_qt.download_files_from_server(
                    parent_widget, get_server_url(),
                    response['files_to_download'],
                    response.get('server_file_hashes', None))
            else:
                QMessageBox.critical(
                    parent_widget, "错误",
                    f"错误响应：{response}\n请重试或联系开发者")
                logger.error(f"错误响应：{response}\n请重试或联系开发者")
        finally:
            worker.deleteLater()

    worker.done.connect(on_done)
    worker.start()
