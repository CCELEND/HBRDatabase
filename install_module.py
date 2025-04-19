import sys
import os
import subprocess
import importlib
from tkinter import messagebox

try:
    pip_args = [
        sys.executable, "-m", "pip", "install",
        "ttkbootstrap", "opencv-python", "pillow", "requests", "pygame", "numpy", "pandas", "openpyxl", "selenium", "webdriver-manager"
        ,"-i", "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华镜像
        "--trusted-host", "pypi.tuna.tsinghua.edu.cn"      # 避免 SSL 错误
    ]
    subprocess.check_call(pip_args)
    messagebox.showinfo("提示", "模块已安装")
except Exception as e:
    messagebox.showerror("错误", f"请重试 {str(e)}")