import asyncio
import json
import time
import os
import hashlib
import traceback
import base64
import requests
from tkinter import messagebox

from urllib.parse import quote

from tools import creat_directory, confirm_restart
        
# 将文件哈希值字典发送到服务器
def send_hashes_to_server(server_url, client_file_hashes):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(client_file_hashes), headers=headers)
    return response.json()

# 从服务器下载文件
def download_files_from_server(server_url, files_to_download):
    if files_to_download:
        err_flag = False
        err_info = ""
        file = ""
        for file_name in files_to_download:
            file = file_name
            creat_directory(file_name)

            # 编码特殊字符
            encoded_name = quote(file_name)
            # 服务器响应
            response = requests.get(f"{server_url}/download/{encoded_name}")

            if response.content.startswith(b'{"error"'):
                err_info = response.content.decode('utf-8')
                err_flag = True
                break

            # 保存文件
            with open(file_name, 'wb') as f:
                f.write(response.content)
            print(f"更新：'{file_name}'")

        if err_flag:
            messagebox.showerror("错误", f"文件 '{file}' 下载失败\n请重试 {err_info}")
        else:
            confirm_restart("更新完成")
    else:
        messagebox.showinfo("提示", "已是最新版本")