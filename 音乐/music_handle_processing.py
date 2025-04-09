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

import music_player

# 检查目录是否存在，如果不存在则创建
def creat_directory(file_name):
    # 获取目录路径
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

server_url = "http://47.96.235.36:65431"

def download_music_files_from_server(file_path_ost):
    file_path_all = "./音乐/下载/" + file_path_ost
    creat_directory(file_path_all)

    # 编码特殊字符
    encoded_name = quote(file_path_ost)
    # 服务器响应
    response = requests.get(f"{server_url}/music_download/{encoded_name}")

    if response.content.startswith(b'{"error"'):
        err_info = response.content.decode('utf-8')
        messagebox.showerror("错误", f"文件 '{file_path_ost}' 下载失败\n请重试 {err_info}")
        return False

    # 保存文件
    with open(file_path_all, 'wb') as f:
        f.write(response.content)

    return True

# Tkinter 是单线程的 GUI，所有 UI 更新（如按钮状态变化）必须在主线程中完成
# 确保操作在主线程中执行
def safe_stop():
    if music_player.PlayerApp:
        music_player.PlayerApp.frame.after(0, music_player.PlayerApp.stop)
        # 等待 Tkinter 处理事件队列
        music_player.PlayerApp.frame.update_idletasks()

def music_handle(file_path_ost):
    file_path_all = "./音乐/下载/" + file_path_ost
    if not os.path.exists(file_path_all):
        if not download_music_files_from_server(file_path_ost):
            safe_stop()
            return

    safe_stop()
    music_player.PlayerApp.frame.after(0, lambda: music_player.PlayerApp.load_file(file_path_all))
