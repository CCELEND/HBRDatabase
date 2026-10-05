
from tkinter import messagebox

from tools import get_os_info
from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

# 兼容两种导入方式：项目根目录在 sys.path 上（from 更新.xxx）时，
# 或 ./更新 在 sys.path 上（from xxx）时，都能正常导入。
try:
    from 更新.hash import calculate_file_hashes
    from 更新.http_client import send_hashes_to_server, download_files_from_server
    from 更新.server_config import server_url as get_server_url
    import 更新.http_client as http_client
except ImportError:                                   # pragma: no cover
    from hash import calculate_file_hashes
    from http_client import send_hashes_to_server, download_files_from_server
    from server_config import server_url as get_server_url
    import http_client

def http_update_data():

    if http_client.is_updating:
        return
        
    current_file_hashes = calculate_file_hashes("./")
    # 地址与 https 配置见 更新/server_config.py（可用环境变量覆盖）
    server_url = get_server_url()
    sys = get_os_info()
    response = None
    try:
        # 发送哈希值到服务器
        response = send_hashes_to_server(server_url, current_file_hashes, "update", sys)
    except Exception as e:
        logger.error(f"连接失败：{str(e)}\n请重试或联系开发者")
        messagebox.showerror("错误", f"连接失败：{str(e)}\n请重试或联系开发者")

    # 下载服务器返回的需要更新的文件
    if response and 'files_to_download' in response:
        download_files_from_server(server_url, response['files_to_download'], response.get('server_file_hashes', None))
    else:
        messagebox.showerror("错误", f"错误响应：{response}\n请重试或联系开发者")
        logger.error(f"错误响应：{response}\n请重试或联系开发者")


