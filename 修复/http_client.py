import sys
import json
import requests
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from threading import Thread

from window import set_window_icon, creat_window
from tools import sort_dict_by_key
from 修复.hash import save_hashes_to_json
from 更新.download_utils import download_file, expected_hash_for
from 更新.local_policy import (
    filter_local_only_files, filter_local_only_hashes)
from 更新.server_config import requests_kwargs as _tls_kwargs

from 日志.advanced_logger import AdvancedLogger

logger = AdvancedLogger.get_logger(__name__)
is_updating = False

# 将文件哈希值字典发送到服务器
def send_hashes_to_server(server_url, client_file_hashes, oper="repair", sys="windows"):
    headers = {'Content-Type': 'application/json'}
    payload = {"ver": "PyQT5", "oper": oper, "sys": sys, "hashes": client_file_hashes}
    response = requests.post(server_url, data=json.dumps(payload), headers=headers,
                             timeout=5, **_tls_kwargs())
    return response.json()

def create_progress_window():
    # 创建进度窗口
    progress_window = creat_window("修复", 600, 166, 440, 50)
    set_window_icon(progress_window, "./修复/net.ico")
    
    # 进度条
    progress = ttk.Progressbar(progress_window, orient="horizontal", 
                             length=500, mode="determinate")
    progress.pack(pady=20, padx=20)
    
    # 状态标签
    status_var = tk.StringVar()
    status_var.set("正在下载修复资源...")
    status_label = tk.Label(progress_window, textvariable=status_var)
    status_label.pack()
    
    # 进度百分比
    percent_var = tk.StringVar()
    percent_var.set("0%")
    percent_label = tk.Label(progress_window, textvariable=percent_var)
    percent_label.pack()
    
    # 当前文件标签
    file_var = tk.StringVar()
    file_label = tk.Label(progress_window, textvariable=file_var)
    file_label.pack(pady=10)
    
    return progress_window, progress, status_var, percent_var, file_var

def handle_download_completion(progress_window, progress, status_var):
    # 下载完成后
    if progress['value'] >= progress['maximum']:
        global is_updating
        is_updating = False
        status_var.set("修复完成！")
        messagebox.showinfo("提示", "成功修复与重置")
        progress_window.destroy()
        progress_window.quit()
        sys.exit()
    else:
        progress_window.after(100, lambda: handle_download_completion(
            progress_window, progress, status_var
        ))

def download_single_file(file_name, i, total_files, server_url,
                          server_file_hashes, progress, percent_var, file_var,
                          progress_window):
    # 下载单个文件
    try:
        file_var.set(f"下载修复资源：'{file_name}' ({i+1}/{total_files})")
        progress_window.update()

        expected = expected_hash_for(server_file_hashes, file_name)

        def on_progress(downloaded, total_size):
            update_progress(i, total_files, downloaded, total_size,
                            progress, percent_var, progress_window)

        # 先写临时文件，校验 SHA-256 后再原子替换旧文件。
        download_file(
            server_url,
            file_name,
            expected_hash=expected,
            require_hash=bool(server_file_hashes),
            progress_hook=on_progress,
        )
        return True

    except Exception as e:
        handle_download_error(file_name, e)
        return False

def update_progress(file_index, total_files, downloaded, total_size,
                    progress, percent_var, progress_window):
    # 更新进度显示
    if total_size > 0:
        file_progress = int(downloaded / total_size * 100)
        overall_progress = file_index * 100 + file_progress
        progress['value'] = overall_progress
        percent_var.set(f"{int(overall_progress / total_files)}%")
        progress_window.update()

def handle_download_error(file_name, error):
    # 处理下载错误
    logger.error(f"'{file_name}' 下载失败\n请重试 {str(error)}")
    messagebox.showerror("错误", f"'{file_name}' 下载失败\n请重试 {str(error)}")
    global is_updating
    is_updating = False

def download_thread(files_to_download, server_url, server_file_hashes,
                    progress_window, progress, status_var, percent_var, file_var):
    # 下载线程
    total_files = len(files_to_download)
    progress['maximum'] = total_files * 100  # 每个文件100单位

    for i, file_name in enumerate(files_to_download):
        success = download_single_file(
            file_name, i, total_files, server_url, server_file_hashes,
            progress, percent_var, file_var, progress_window)

        if not success:
            progress_window.destroy()
            return

        # 完成一个文件，增加进度
        progress['value'] = (i + 1) * 100
        percent_var.set(f"{int((i + 1) / total_files * 100)}%")
        progress_window.update()

    # 全部文件成功后才更新本地服务器清单。
    if server_file_hashes:
        sorted_hashes = sort_dict_by_key(server_file_hashes)
        save_hashes_to_json(sorted_hashes, "./关于/server_file_hashes.json")

    # 下载完成后检查状态
    handle_download_completion(progress_window, progress, status_var)

def download_files_with_progress(files_to_download, server_url,
                                 server_file_hashes=None):
    global is_updating
    is_updating = True

    # 创建进度窗口
    progress_window, progress, status_var, percent_var, file_var = create_progress_window()

    # 在新线程中执行下载
    Thread(target=download_thread, args=(
        files_to_download, server_url, server_file_hashes, progress_window,
        progress, status_var, percent_var, file_var
    ), daemon=True).start()

    progress_window.mainloop()

# 从服务器下载文件
def download_files_from_server(server_url, files_to_download, server_file_hashes):

    # 服务器清单可能来自旧版本或被误配置；本机配置文件绝不能参与下载。
    files_to_download = filter_local_only_files(files_to_download or [])
    server_file_hashes = filter_local_only_hashes(server_file_hashes)

    if not files_to_download:
        messagebox.showinfo("提示", "未发现资源完整性冲突")
        return

    download_files_with_progress(
        files_to_download, server_url, server_file_hashes)