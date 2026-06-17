
from 更新.hash import calculate_file_hashes, save_hashes_to_json
from tkinter import messagebox
import threading

from 更新.http_client import send_hashes_to_server
from tools import sort_dict_by_key

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def check_for_updates_proc():
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
            server_file_datetime = response.get('server_file_datetime', None)
            server_file_hashes = response.get('server_file_hashes', None)
            print(f"[!] 检测到资源冲突或存在新版本，请更新！\n版本时间戳：{server_file_datetime}")
            messagebox.showinfo("提示", f"检测到资源冲突或存在新版本，请更新！\n版本时间戳：{server_file_datetime}")

            if server_file_hashes:
                server_file_hashes = sort_dict_by_key(server_file_hashes)
                save_hashes_to_json(server_file_hashes, "./关于/server_file_hashes.json")
    else:
        messagebox.showerror("错误", f"错误响应：{response}\n请重试或联系开发者")
        logger.error(f"错误响应：{response}\n请重试或联系开发者")

def check_for_updates():
    print("[*] 启动更新检查线程...")
    proc_thread = threading.Thread(target=check_for_updates_proc, daemon=False)
    proc_thread.start()



