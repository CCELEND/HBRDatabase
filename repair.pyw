
from tkinter import messagebox
from 修复.hash import calculate_file_hashes
from 修复.http_client import send_hashes_to_server, download_files_from_server

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def repair_reset():
        
    current_file_hashes = calculate_file_hashes("./")
    server_url = "http://47.96.235.36:65433"

    # 发送哈希值到服务器
    response = send_hashes_to_server(server_url, current_file_hashes)

    # 下载服务器返回的需要更新的文件
    if 'files_to_download' in response:
        download_files_from_server(server_url, response['files_to_download'])
    else:
        logger.error(f"错误响应：{response}\n请重试或联系开发者")
        messagebox.showerror("错误", f"错误响应：{response}\n请重试或联系开发者")
        
if __name__ == "__main__":
    repair_reset()
    

