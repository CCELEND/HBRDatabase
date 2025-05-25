
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

def install_modules():
    mirrors = [
        {"url": "https://pypi.tuna.tsinghua.edu.cn/simple", "host": "pypi.tuna.tsinghua.edu.cn"},
        {"url": "https://mirrors.aliyun.com/pypi/simple", "host": "mirrors.aliyun.com"}
    ]
    
    packages = [
        "ttkbootstrap", "opencv-python", "pillow", "requests", 
        "pygame", "numpy", "pandas", "openpyxl", 
        "selenium", "webdriver-manager"
    ]
    
    for mirror in mirrors:
        try:
            pip_args = [
                sys.executable, "-m", "pip", "install",
                *packages,
                "-i", mirror["url"],
                "--trusted-host", mirror["host"]
            ]
            
            subprocess.check_call(pip_args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            messagebox.showinfo("提示", "依赖模块已成功安装")
            return True
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("错误", f"使用镜像 {mirror['url']} 安装失败: {e}")
            continue
        except Exception as e:
            messagebox.showerror("错误", f"发生未知错误: {e}")
            continue
    
    # 所有镜像都失败
    messagebox.showerror("错误", "所有镜像源尝试失败，请检查网络连接或手动安装")
    return False

if __name__ == "__main__":
    install_modules()
    

