import sys
import os
import subprocess
import platform
import venv
from importlib import metadata
from tkinter import messagebox

# 虚拟环境自动管理
def ensure_venv(venv_dir="venv"):
    """
    确保脚本运行在虚拟环境中。
    若当前不在虚拟环境，则创建（或使用）指定目录的 venv，
    并用该 venv 的 Python 重新执行本脚本。
    """
    # 检查是否已在虚拟环境
    if sys.prefix != sys.base_prefix:
        print("[+] 当前已在虚拟环境中")
        return True

    print("[*] 当前未在虚拟环境中，准备自动切换到虚拟环境...")

    # 确定虚拟环境路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(base_dir, venv_dir)

    # 如果虚拟环境不存在，则创建
    if not os.path.exists(venv_path):
        print(f"[*] 创建虚拟环境: {venv_path}")
        # 使用 venv 标准库创建（继承当前 Python 版本）
        builder = venv.EnvBuilder(system_site_packages=False, clear=False)
        builder.create(venv_path)
    else:
        print(f"[*] 使用已存在的虚拟环境: {venv_path}")

    # 获取虚拟环境中的 Python 解释器路径
    if platform.system() == "Windows":
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(venv_path, "bin", "python")

    if not os.path.exists(python_exe):
        print(f"[-] 未找到虚拟环境的 Python 解释器: {python_exe}")
        return False

    # 用虚拟环境的 Python 重新执行当前脚本，并传递原有参数
    script_path = os.path.abspath(__file__)
    args = [python_exe, script_path] + sys.argv[1:]
    print(f"[*] 重新执行: {' '.join(args)}")
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] 重新执行失败: {e}")
        sys.exit(1)

    sys.exit(0)


def _installed_version(package_name):
    """读取已安装版本；未安装返回 None（不启动 pip 子进程）。"""
    try:
        return metadata.version(package_name.replace("_", "-"))
    except (metadata.PackageNotFoundError, ValueError):
        return None
    except Exception:
        return None


def _needs_install(requirement):
    """requirement 形如 package 或 package==version。"""
    if "==" in requirement:
        name, wanted = requirement.split("==", 1)
        return _installed_version(name) != wanted
    return _installed_version(requirement) is None


def check_ttkbootstrap_version():
    current_version = _installed_version("ttkbootstrap")
    if current_version is None:
        print("[-] ttkbootstrap 未安装")
        return None, None
    if current_version == "1.12.0":
        print(f"[+] ttkbootstrap 版本正确: {current_version}")
        return True, current_version
    print(f"[!] ttkbootstrap 版本不匹配: 当前{current_version}, 需要1.12.0")
    return False, current_version

def uninstall_ttkbootstrap():

    try:
        print("[*] 正在卸载 ttkbootstrap...")
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "ttkbootstrap", "-y"],
            capture_output=True,
            text=True,
            check=True
        )
        print("[+] ttkbootstrap 卸载成功.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] 卸载 ttkbootstrap 失败: {e}")
        return False

def install_modules():
    mirrors = [
        {"url": "https://pypi.tuna.tsinghua.edu.cn/simple", "host": "pypi.tuna.tsinghua.edu.cn"},
        {"url": "https://mirrors.aliyun.com/pypi/simple", "host": "mirrors.aliyun.com"},
        {"url": "https://pypi.douban.com/simple", "host": "pypi.douban.com"},
        {"url": "https://pypi.org/simple", "host": "pypi.org"}
    ]
    
    packages = [
        "setuptools==75.8.1","PyQt5","psutil",
        "ttkbootstrap==1.12.0", "opencv_python==4.11.0.86", "pillow==11.1.0", "Requests==2.32.3", 
        "pygame==2.6.1", "numpy==2.1.3", "pandas==2.2.3", "openpyxl==3.1.5", 
        "selenium==4.33.0", "webdriver-manager==4.0.2"
    ]
    
    ttkbootstrap_status, current_version = check_ttkbootstrap_version()
    
    if ttkbootstrap_status is True:
        packages = [pkg for pkg in packages if not pkg.startswith("ttkbootstrap==")]
    elif ttkbootstrap_status is False:
        print(f"[!] ttkbootstrap 版本不正确: {current_version}，需要卸载后重新安装")
        if not uninstall_ttkbootstrap():
            messagebox.showwarning("警告", "ttkbootstrap 卸载失败，将继续尝试安装正确版本")

    # 只安装缺失/版本不符的包；全部满足时不再访问镜像源
    packages = [pkg for pkg in packages if _needs_install(pkg)]
    
    if not packages:
        messagebox.showinfo("提示", "所有依赖模块已安装且版本正确")
        return True
    
    print(f"[*] 需要安装的包: {packages}")
    
    for mirror in mirrors:
        try:
            pip_args = [
                sys.executable, "-m", "pip", "install",
                *packages,
                "-i", mirror["url"],
                "--trusted-host", mirror["host"],
                "--timeout", "60",
                "--retries", "3"
            ]
            print(f"[*] 尝试使用镜像: {mirror['url']}")
            subprocess.check_call(pip_args)
            
            if "ttkbootstrap==1.12.0" in packages:
                ttkbootstrap_status, final_version = check_ttkbootstrap_version()
                if ttkbootstrap_status:
                    messagebox.showinfo("提示", "依赖模块已成功安装，ttkbootstrap 版本正确")
                else:
                    messagebox.showwarning("警告", f"模块安装完成，但 ttkbootstrap 版本可能不正确 (当前: {final_version})")
            else:
                # messagebox.showinfo("提示", "依赖模块已成功安装")
                print("[+] 依赖模块已成功安装.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[-] 使用镜像 {mirror['url']} 安装失败: {e}")
            continue
        except Exception as e:
            print(f"[-] 发生未知错误: {e}")
            continue
    
    messagebox.showerror("错误", "所有镜像源尝试失败，请检查网络连接或手动安装")
    return False


if __name__ == "__main__":
    # 先确保运行在虚拟环境中
    if not ensure_venv():
        sys.exit(1)
    # 然后执行安装任务
    install_modules()