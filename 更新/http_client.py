
import json
import requests
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from threading import Thread

from window import set_window_icon
from tools import confirm_restart, sort_dict_by_key
from 更新.download_utils import (
    DownloadCancelled, download_file, expected_hash_for)
from 更新.hash import save_hashes_to_json
from 更新.local_policy import (
    filter_local_only_files, filter_local_only_hashes)
from 更新.server_config import requests_kwargs as _tls_kwargs

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

is_updating = False
        
# 将文件哈希值字典发送到服务器
def send_hashes_to_server(server_url, client_file_hashes, oper="update", sys="windows"):
    headers = {'Content-Type': 'application/json'}
    payload = {"ver": "tkinter", "oper": oper, "sys": sys, "hashes": client_file_hashes}
    response = requests.post(server_url, data=json.dumps(payload), headers=headers,
                             timeout=5, **_tls_kwargs())
    return response.json()

def download_files_with_progress(files_to_download, server_url,
                                 server_file_hashes=None):

    global is_updating
    # 创建进度窗口
    progress_window = tk.Toplevel()
    progress_window.title("更新")
    progress_window.geometry("600x166")
    set_window_icon(progress_window, "./更新/net.ico")

    # 进度条
    progress = ttk.Progressbar(progress_window, orient="horizontal",
                             length=500, mode="determinate")
    progress.pack(pady=20, padx=20)

    # 状态标签
    status_var = tk.StringVar()
    status_var.set("正在下载更新资源...")
    status_label = tk.Label(progress_window, textvariable=status_var)
    status_label.pack()

    # 进度百分比
    percent_var = tk.StringVar()
    percent_var.set("0%")
    percent_label = tk.Label(progress_window, textvariable=percent_var)
    percent_label.pack()

    # 当前文件标签
    file_var = tk.StringVar()
    file_var.set("")
    file_label = tk.Label(progress_window, textvariable=file_var)
    file_label.pack(pady=10)

    def check_completion():
        if progress['value'] < progress['maximum']:
            progress_window.after(100, check_completion)
        else:
            global is_updating
            is_updating = False
            status_var.set("更新完成！")
            confirm_restart("更新完成")

    def download_thread():
        total_files = len(files_to_download)
        progress['maximum'] = total_files * 100  # 每个文件100单位

        for i, file_name in enumerate(files_to_download):
            try:
                file_var.set(f"下载更新：'{file_name}' ({i+1}/{total_files})")
                progress_window.update()

                expected = expected_hash_for(server_file_hashes, file_name)

                def on_progress(downloaded, total_size):
                    if total_size > 0:
                        file_progress = int(downloaded / total_size * 100)
                        overall_progress = i * 100 + file_progress
                        progress['value'] = overall_progress
                        percent_var.set(f"{int(overall_progress / total_files)}%")
                        progress_window.update()

                # 先写临时文件，校验 SHA-256 后再原子替换旧文件。
                download_file(
                    server_url,
                    file_name,
                    expected_hash=expected,
                    require_hash=bool(server_file_hashes),
                    progress_hook=on_progress,
                )
            except DownloadCancelled:
                is_updating = False
                progress_window.destroy()
                return
            except Exception as e:
                logger.error(f"'{file_name}' 下载失败\n请重试 {str(e)}")
                messagebox.showerror("错误", f"'{file_name}' 下载失败\n请重试 {str(e)}")
                is_updating = False
                progress_window.destroy()
                return
            else:
                # 完成一个文件，增加进度
                progress['value'] = (i + 1) * 100
                percent_var.set(f"{int((i + 1) / total_files * 100)}%")
                progress_window.update()

        # 全部文件成功后才更新本地服务器清单。
        if progress['value'] >= progress['maximum'] and server_file_hashes:
            sorted_hashes = sort_dict_by_key(server_file_hashes)
            save_hashes_to_json(sorted_hashes, "./关于/server_file_hashes.json")

        # 下载完成后检查状态
        check_completion()

    # 在新线程中执行下载
    Thread(target=download_thread, daemon=True).start()


# 从服务器下载文件
def download_files_from_server(server_url, files_to_download, server_file_hashes):

    # 服务器清单可能来自旧版本或被误配置；本机配置文件绝不能参与下载。
    files_to_download = filter_local_only_files(files_to_download or [])
    server_file_hashes = filter_local_only_hashes(server_file_hashes)

    if files_to_download:
        global is_updating
        is_updating = True
        download_files_with_progress(
            files_to_download, server_url, server_file_hashes)

    else:
        messagebox.showinfo("提示", "已是最新版本")
        