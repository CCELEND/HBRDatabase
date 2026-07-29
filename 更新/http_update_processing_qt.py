from 更新.hash import calculate_file_hashes
from 更新.http_client_qt import send_hashes_to_server, download_files_from_server
import 更新.http_client_qt as http_client_qt
from PyQt5.QtWidgets import QMessageBox
from 日志.advanced_logger import AdvancedLogger

logger = AdvancedLogger.get_logger(__name__)

def http_update_data(parent_widget):
    if http_client_qt.is_updating():
        return

    current_file_hashes = calculate_file_hashes("./")
    server_url = "http://47.96.235.36:65433"

    try:
        response = send_hashes_to_server(server_url, current_file_hashes)
    except Exception as e:
        logger.error(f"连接失败：{str(e)}\n请重试或联系开发者")
        QMessageBox.critical(parent_widget, "错误", f"连接失败：{str(e)}\n请重试或联系开发者")
        return

    if 'files_to_download' in response:
        http_client_qt.download_files_from_server(parent_widget, server_url,
                                   response['files_to_download'],
                                   response.get('server_file_hashes', None))
    else:
        QMessageBox.critical(parent_widget, "错误", f"错误响应：{response}\n请重试或联系开发者")
        logger.error(f"错误响应：{response}\n请重试或联系开发者")