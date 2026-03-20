
from hash import calculate_file_hashes
from tkinter import messagebox

from http_client import send_hashes_to_server

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def check_for_updates():

    current_file_hashes = calculate_file_hashes("./")
    # server_url = "http://127.0.0.1:65433"
    server_url = "http://47.96.235.36:65433"

    try:
        # 发送哈希值到服务器
        response = send_hashes_to_server(server_url, current_file_hashes)
    except Exception as e:
        logger.error(f"连接失败：{str(e)}\n请重试或联系开发者")
        messagebox.showerror("错误", f"连接失败：{str(e)}\n请重试或联系开发者")

    # 下载服务器返回的需要更新的文件
    if 'files_to_download' in response:
        if response['files_to_download']:
            messagebox.showinfo("信息", f"发现新版本，请更新")
    else:
        messagebox.showerror("错误", f"错误响应：{response}\n请重试或联系开发者")
        logger.error(f"错误响应：{response}\n请重试或联系开发者")


