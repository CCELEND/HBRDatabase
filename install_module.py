import sys
import subprocess
from tkinter import messagebox

def check_ttkbootstrap_version():
    # 检查 ttkbootstrap 版本是否为1.12.0，返回状态和版本信息
    try:
        # 检查当前安装的 ttkbootstrap 版本
        result = subprocess.run(
            [sys.executable, "-c", "import pkg_resources; print(pkg_resources.get_distribution('ttkbootstrap').version)"],
            capture_output=True,
            text=True,
            check=True
        )
        current_version = result.stdout.strip()
        if current_version == "1.12.0":
            print(f"[+] ttkbootstrap 版本正确: {current_version}")
            return True, current_version  # 版本正确
        else:
            print(f"[!] ttkbootstrap 版本不匹配: 当前{current_version}, 需要1.12.0")
            return False, current_version  # 版本不正确
            
    except subprocess.CalledProcessError:
        print("[-] ttkbootstrap 未安装")
        return None, None  # 未安装
    except Exception as e:
        print(f"[-] 检查版本时出错: {e}")
        return None, None  # 检查失败

def uninstall_ttkbootstrap():
    # 卸载 ttkbootstrap
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
        {"url": "https://pypi.org/simple", "host": "pypi.org"}  # 官方源
    ]
    
    packages = [
        "setuptools==75.8.1",
        "ttkbootstrap==1.12.0", "opencv_python==4.11.0.86", "pillow==11.1.0", "Requests==2.32.3", 
        "pygame==2.6.1", "numpy==2.1.3", "pandas==2.2.3", "openpyxl==3.1.5", 
        "selenium==4.33.0", "webdriver-manager==4.0.2"
    ]
    
    # 检查 ttkbootstrap 版本状态
    ttkbootstrap_status, current_version = check_ttkbootstrap_version()
    
    if ttkbootstrap_status is True:
        packages = [pkg for pkg in packages if not pkg.startswith("ttkbootstrap==")]
    elif ttkbootstrap_status is False:
        # 版本不正确，需要卸载后重新安装
        print(f"[!] ttkbootstrap 版本不正确: {current_version}，需要卸载后重新安装")
        if not uninstall_ttkbootstrap():
            messagebox.showwarning("警告", "ttkbootstrap 卸载失败，将继续尝试安装正确版本")
    
    # 如果没有需要安装的包
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
                "--timeout", "60",  # 增加超时时间
                "--retries", "3"    # 增加重试次数
            ]
            
            print(f"[*] 尝试使用镜像: {mirror['url']}")
            subprocess.check_call(pip_args)
            
            # 检查 ttkbootstrap版本
            if "ttkbootstrap==1.12.0" in packages:
                ttkbootstrap_status, final_version = check_ttkbootstrap_version()
                if ttkbootstrap_status:
                    messagebox.showinfo("提示", "依赖模块已成功安装，ttkbootstrap 版本正确")
                else:
                    messagebox.showwarning("警告", f"模块安装完成，但 ttkbootstrap 版本可能不正确 (当前: {final_version})")
            else:
                messagebox.showinfo("提示", "依赖模块已成功安装")
                
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[-] 使用镜像 {mirror['url']} 安装失败: {e}")
            continue
        except Exception as e:
            print(f"[-] 发生未知错误: {e}")
            continue
    
    # 所有镜像都失败
    messagebox.showerror("错误", "所有镜像源尝试失败，请检查网络连接或手动安装")
    return False

if __name__ == "__main__":
    install_modules()