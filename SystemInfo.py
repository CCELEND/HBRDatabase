import os
import sys
import platform
import psutil
import subprocess

# pip install psutil
# pip install pipreqs

def get_basic_info():
    # 获取基本系统信息
    basic_info = "\n===== 基本系统信息 =====\n"
    basic_info += f"操作系统名称：{platform.system()}\n" # Windows/Linux/macOS
    basic_info += f"操作系统版本：{platform.release()}\n" # Windows 10/11 的版本号
    basic_info += f"操作系统详细版本：{platform.version()}\n" # 版本描述
    basic_info += f"主机名：{platform.node()}\n" # 计算机名称
    basic_info += f"硬件架构：{platform.machine()}\n"
    basic_info += f"Python 版本：{sys.version.split()[0]}\n" # Python 解释器版本
    basic_info += f"Python 路径：{sys.executable}\n" # Python 解释器位置
    return basic_info


def get_cpu_info():
    # 获取CPU信息
    cpu_info = "\n===== CPU 信息 =====\n"
    cpu_info += f"物理核心数：{psutil.cpu_count(logical=False)}\n"  # 实际物理CPU核心数
    cpu_info += f"逻辑核心数：{psutil.cpu_count(logical=True)}\n"  # 含超线程的逻辑核心数
    cpu_info += f"CPU 当前使用率：{psutil.cpu_percent(interval=1)}%\n"  # 间隔1秒的使用率
    cpu_info += "CPU 时间分配（用户/系统/空闲）：\n"
    cpu_times = psutil.cpu_times()
    cpu_info += f"    用户态：{cpu_times.user:.2f}s，系统态：{cpu_times.system:.2f}s，空闲：{cpu_times.idle:.2f}s\n"
    return cpu_info


def get_memory_info():
    # 获取内存信息
    memory_info = "\n===== 内存信息 =====\n"
    virtual_mem = psutil.virtual_memory()
    total_mem = virtual_mem.total / (1024 **3)  # 转换为GB
    available_mem = virtual_mem.available / (1024** 3)
    used_mem = virtual_mem.used / (1024 **3)
    memory_info += f"总内存：{total_mem:.2f} GB\n"
    memory_info += f"可用内存：{available_mem:.2f} GB\n"
    memory_info += f"已用内存：{used_mem:.2f} GB\n"
    memory_info += f"内存使用率：{virtual_mem.percent}%\n"
    

    # 虚拟内存信息
    swap_mem = psutil.swap_memory()
    total_swap = swap_mem.total / (1024** 3)
    memory_info += f"\n交换内存总大小：{total_swap:.2f} GB\n"
    memory_info += f"交换内存使用率：{swap_mem.percent}%\n"
    return memory_info

def get_disk_info():
    # 获取磁盘信息
    disk_info = "\n===== 磁盘信息 =====\n"
    # 所有磁盘分区
    partitions = psutil.disk_partitions()
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue  # 跳过无权限的分区
        total_disk = usage.total / (1024 **3)  # GB
        used_disk = usage.used / (1024** 3)
        disk_info += f"分区：{part.device}（挂载点：{part.mountpoint}）\n"
        disk_info += f"    总大小：{total_disk:.2f} GB，已用：{used_disk:.2f} GB，使用率：{usage.percent}%\n"

    # 磁盘IO总情况
    disk_io = psutil.disk_io_counters()
    disk_info += f"\n磁盘读写：读{disk_io.read_bytes/(1024**3):.2f}GB，写{disk_io.write_bytes/(1024**3):.2f}GB\n"
    return disk_info


def get_network_info():
    # 获取网络信息
    network_info = "\n===== 网络信息 =====\n"
    # 网络接口IP地址
    net_if_addrs = psutil.net_if_addrs()
    for if_name, addrs in net_if_addrs.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # 只获取IPv4地址
                network_info += f"网卡：{if_name}，IPv4地址：{addr.address}\n"

    # 网络流量情况
    net_io = psutil.net_io_counters()
    network_info += f"\n网络流量：接收{net_io.bytes_recv/(1024**3):.2f}GB，发送{net_io.bytes_sent/(1024**3):.2f}GB\n"
    return network_info


def get_py_info():
    # 获取python模块信息
    py_info = "\n===== python模块信息 =====\n"
    # pipreqs ./ --encoding=utf8 --print
    args = ["pipreqs", "./", "--encoding=utf8", "--print"
    ]
    # subprocess.check_call(args)
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True
    )
    py_info += result.stdout
    return py_info


if __name__ == "__main__":
    import socket
    print("[*] 正在获取系统信息...")
    info = ""
    info += get_basic_info()
    info += get_cpu_info()
    info += get_memory_info()
    info += get_disk_info()
    info += get_network_info()
    info += get_py_info()
    print(info)
    input("按任意键继续...\n")
