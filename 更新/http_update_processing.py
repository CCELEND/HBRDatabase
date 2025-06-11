
from hash import calculate_file_hashes
from tkinter import messagebox

from http_client import send_hashes_to_server, download_files_from_server
import http_client

def http_update_data():

    if http_client.is_updating:
        return
        
    current_file_hashes = calculate_file_hashes("./")
    # server_url = "http://127.0.0.1:65433"
    server_url = "http://47.96.235.36:65433"

    # 发送哈希值到服务器
    response = send_hashes_to_server(server_url, current_file_hashes)

    # 下载服务器返回的需要更新的文件
    if 'files_to_download' in response:
        download_files_from_server(server_url, response['files_to_download'])
    else:
        messagebox.showerror("错误", f"错误响应：{response.content}\n请重试")


