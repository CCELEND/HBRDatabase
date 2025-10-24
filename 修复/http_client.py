import sys
import json
import requests
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from threading import Thread
from urllib.parse import quote

from window import set_window_icon, creat_window
from tools import creat_directory

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

is_updating = False
        
# 将文件哈希值字典发送到服务器
def send_hashes_to_server(server_url, client_file_hashes):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(client_file_hashes), headers=headers, timeout=5)
    return response.json()

def download_files_with_progress(files_to_download, server_url):

    global is_updating
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
    file_var.set("")
    file_label = tk.Label(progress_window, textvariable=file_var)
    file_label.pack(pady=10)
    
    def check_completion():
        if progress['value'] < progress['maximum']:
            progress_window.after(100, check_completion)
        else:
            global is_updating
            is_updating = False
            status_var.set("修复完成！")
            messagebox.showinfo("提示", "成功修复与重置")
            progress_window.destroy()  # 先销毁窗口
            progress_window.quit()  # 停止主循环
            sys.exit()
    
    def download_thread():
        total_files = len(files_to_download)
        progress['maximum'] = total_files * 100  # 每个文件100单位
        
        for i, file_name in enumerate(files_to_download):
            try:
                file_var.set(f"下载修复资源：'{file_name}' ({i+1}/{total_files})")
                progress_window.update()
                
                # 创建目录
                creat_directory(file_name)
                
                # 编码特殊字符
                encoded_name = quote(file_name)
                url = f"{server_url}/download/{encoded_name}"
                
                # 流式下载
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    
                    # 检查是否是错误响应
                    if response.status_code != 200:
                        err_info = response.json()
                        logger.error(f"{err_info.get('error', '未知错误')}")
                        messagebox.showerror("错误", f"{err_info.get('error', '未知错误')}")
                        global is_updating
                        is_updating = False
                        progress_window.destroy()
                        break
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    # 保存文件
                    with open(file_name, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # 过滤掉保持连接的空白块
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 更新进度
                                if total_size > 0:
                                    file_progress = int(downloaded / total_size * 100)
                                    overall_progress = i * 100 + file_progress
                                    progress['value'] = overall_progress
                                    percent_var.set(f"{int(overall_progress / total_files)}%")
                                    progress_window.update()
            
            except Exception as e:
                logger.error(f"'{file_name}' 下载失败\n请重试 {str(e)}")
                messagebox.showerror("错误", f"'{file_name}' 下载失败\n请重试 {str(e)}")
                is_updating = False
                progress_window.destroy()
                break
            else:
                # 完成一个文件，增加进度
                progress['value'] = (i + 1) * 100
                percent_var.set(f"{int((i + 1) / total_files * 100)}%")
                progress_window.update()
        
        # 下载完成后检查状态
        check_completion()
    
    # 在新线程中执行下载
    Thread(target=download_thread, daemon=True).start()

    progress_window.mainloop()


# 从服务器下载文件
def download_files_from_server(server_url, files_to_download):
    if files_to_download:
        global is_updating
        is_updating = True
        download_files_with_progress(files_to_download, server_url)

    else:
        messagebox.showinfo("提示", "未发现资源完整性冲突")
        