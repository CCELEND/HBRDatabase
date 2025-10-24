
from hash import calculate_file_hashes
from tkinter import messagebox

from http_client import send_hashes_to_server, download_files_from_server
import http_client

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def http_update_data():

    if http_client.is_updating:
        return
        
    current_file_hashes = calculate_file_hashes("./")
    # server_url = "http://127.0.0.1:65433"
    server_url = "http://47.96.235.36:65433"

    try:
        # 发送哈希值到服务器
        response = send_hashes_to_server(server_url, current_file_hashes)
    except Exception as e:
        logger.error(f"连接失败：{str(e)}\n请重试或联系开发者")
        messagebox.showerror(f"连接失败：{str(e)}\n请重试或联系开发者")

    # 下载服务器返回的需要更新的文件
    if 'files_to_download' in response:
        download_files_from_server(server_url, response['files_to_download'])
    else:
        messagebox.showerror("错误", f"错误响应：{response}\n请重试或联系开发者")
        logger.error(f"错误响应：{response}\n请重试或联系开发者")


