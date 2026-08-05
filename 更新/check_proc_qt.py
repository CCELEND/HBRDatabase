
from 更新.hash import calculate_file_hashes, save_hashes_to_json
import threading

from 更新.http_client_qt import send_hashes_to_server
from tools import sort_dict_by_key, get_database_version

from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


class UpdateMessenger(QObject):
    """在主线程中显示更新提示的跨线程信使"""
    show_info = pyqtSignal(str, str)
    show_error = pyqtSignal(str, str)


_update_messenger = None


def _get_update_messenger():
    """获取/创建主线程的更新提示信使"""
    global _update_messenger
    if _update_messenger is None:
        _update_messenger = UpdateMessenger()
        _update_messenger.show_info.connect(
            lambda title, text: QMessageBox.information(None, title, text)
        )
        _update_messenger.show_error.connect(
            lambda title, text: QMessageBox.critical(None, title, text)
        )
    return _update_messenger


def _app_is_closing():
    qapp = QApplication.instance()
    return qapp is None or qapp.closingDown()


def check_for_updates_proc(messenger):
    current_file_hashes = calculate_file_hashes("./")
    if _app_is_closing():
        return

    # server_url = "http://127.0.0.1:65433"
    server_url = "http://47.96.235.36:65433"

    response = None
    try:
        # 发送哈希值到服务器
        response = send_hashes_to_server(server_url, current_file_hashes, "check")
    except Exception as e:
        if _app_is_closing():
            return
        logger.error(f"连接失败：{str(e)}\n请重试或联系开发者")
        # 通过信号让主线程显示对话框，避免后台线程直接弹窗导致菜单虚影
        messenger.show_error.emit("错误", f"连接失败：{str(e)}\n请重试或联系开发者")
        return

    if _app_is_closing():
        return

    # 下载服务器返回的需要更新的文件
    if response and 'files_to_download' in response:
        if response['files_to_download']:
            server_file_datetime = response.get('server_file_datetime', None)
            print(f"[!] 检测到资源冲突或存在新版本，请更新！\n版本时间戳：{server_file_datetime}")
            # 通过信号让主线程显示对话框
            messenger.show_info.emit("提示", f"检测到资源冲突或存在新版本，请更新！\n版本时间戳：{server_file_datetime}")

        server_file_hashes = response.get('server_file_hashes', None)
        if server_file_hashes:
            server_file_hashes = sort_dict_by_key(server_file_hashes)
            save_hashes_to_json(server_file_hashes, "./关于/server_file_hashes.json")
            print(f"[+] 服务器构建版本：{get_database_version()}")
    else:
        if _app_is_closing():
            return
        messenger.show_error.emit("错误", f"错误响应：{response}\n请重试或联系开发者")
        logger.error(f"错误响应：{response}\n请重试或联系开发者")


def check_for_updates():
    print("[*] 启动更新检查线程...")
    messenger = _get_update_messenger()
    proc_thread = threading.Thread(target=check_for_updates_proc, args=(messenger,), daemon=True)
    proc_thread.start()



