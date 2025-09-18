
import subprocess
import os
from tkinter import messagebox
from tools import run_admin, is_admin

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def load_seed_tools():
    seed_tools_path = os.path.abspath("./工具/GetEntriesGUILocal/seed_tools/seed_tools.exe")

    if not os.path.exists(seed_tools_path):
        error_msg = f"seed_tools.exe 文件不存在：\n{seed_tools_path}"
        messagebox.showerror("文件缺失", error_msg)
        logger.error(error_msg)
        return

    try:
        if not is_admin():
            response = messagebox.askyesno("需要管理员权限", 
                "启动该工具需要管理员权限，是否立即提升？")
            if not response:
                messagebox.showinfo("提示", "未获取管理员权限，seed_tools.exe 启动中止！")
                logger.warning("用户拒绝提升权限，seed_tools.exe 启动中止！")
                return
            else:
                run_admin()

        # subprocess.run(seed_tools_path)
        subprocess.Popen(
            seed_tools_path,
            creationflags=subprocess.CREATE_NEW_CONSOLE,  # 强制创建新控制台
            stdout=None,  # 输出到新控制台
            stderr=None,
            stdin=None
        )
    except Exception as e:
        print(f"[-] {e}")
        logger.error(str(e))


