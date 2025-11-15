import os
import sys
import platform
import psutil

# pip install psutil

def get_basic_info():
    # 获取基本系统信息
    print("===== 基本系统信息 =====")
    print(f"操作系统名称：{platform.system()}")  # Windows/Linux/macOS
    print(f"操作系统版本：{platform.release()}")  # Windows 10/11 的版本号
    print(f"操作系统详细版本：{platform.version()}")  # 版本描述
    print(f"主机名：{platform.node()}")  # 计算机名称
    print(f"硬件架构：{platform.machine()}")  # 如 x86_64（64位）
    print(f"Python 版本：{sys.version.split()[0]}")  # Python 解释器版本
    print(f"Python 路径：{sys.executable}")  # Python 解释器位置


def get_cpu_info():
    # 获取CPU信息
    print("\n===== CPU 信息 =====")
    print(f"物理核心数：{psutil.cpu_count(logical=False)}")  # 实际物理CPU核心数
    print(f"逻辑核心数：{psutil.cpu_count(logical=True)}")  # 含超线程的逻辑核心数
    print(f"CPU 当前使用率：{psutil.cpu_percent(interval=1)}%")  # 间隔1秒的使用率
    print("CPU 时间分配（用户/系统/空闲）：")
    cpu_times = psutil.cpu_times()
    print(f"  用户态：{cpu_times.user:.2f}s，系统态：{cpu_times.system:.2f}s，空闲：{cpu_times.idle:.2f}s")


def get_memory_info():
    # 获取内存信息
    print("\n===== 内存信息 =====")
    virtual_mem = psutil.virtual_memory()
    total_mem = virtual_mem.total / (1024 **3)  # 转换为GB
    available_mem = virtual_mem.available / (1024** 3)
    used_mem = virtual_mem.used / (1024 **3)
    print(f"总内存：{total_mem:.2f} GB")
    print(f"可用内存：{available_mem:.2f} GB")
    print(f"已用内存：{used_mem:.2f} GB")
    print(f"内存使用率：{virtual_mem.percent}%")

    # 虚拟内存信息
    swap_mem = psutil.swap_memory()
    total_swap = swap_mem.total / (1024** 3)
    print(f"\n交换内存总大小：{total_swap:.2f} GB")
    print(f"交换内存使用率：{swap_mem.percent}%")


def get_disk_info():
    # 获取磁盘信息
    print("\n===== 磁盘信息 =====")
    # 所有磁盘分区
    partitions = psutil.disk_partitions()
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue  # 跳过无权限的分区
        total_disk = usage.total / (1024 **3)  # GB
        used_disk = usage.used / (1024** 3)
        print(f"分区：{part.device}（挂载点：{part.mountpoint}）")
        print(f"    总大小：{total_disk:.2f} GB，已用：{used_disk:.2f} GB，使用率：{usage.percent}%")

    # 磁盘IO总情况
    disk_io = psutil.disk_io_counters()
    print(f"\n磁盘总读写：读{disk_io.read_bytes/(1024**3):.2f}GB，写{disk_io.write_bytes/(1024**3):.2f}GB")


def get_network_info():
    # 获取网络信息
    print("\n===== 网络信息 =====")
    # 网络接口IP地址
    net_if_addrs = psutil.net_if_addrs()
    for if_name, addrs in net_if_addrs.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # 只获取IPv4地址
                print(f"网卡：{if_name} 的IPv4地址：{addr.address}")

    # 网络流量总情况
    net_io = psutil.net_io_counters()
    print(f"\n总网络流量：接收{net_io.bytes_recv/(1024**3):.2f}GB，发送{net_io.bytes_sent/(1024**3):.2f}GB")


if __name__ == "__main__":
    import socket
    get_basic_info()
    get_cpu_info()
    get_memory_info()
    get_disk_info()
    get_network_info()
    input()
