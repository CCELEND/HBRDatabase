import sys
import ctypes
import os
import pathlib
from PIL import Image
from tkinter import messagebox
import json
import hashlib
import binascii
import re
import shutil
from pathlib import Path

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

import 日志.error_queue_proc

def get_version():
    version = read_txt_file("./关于/version.txt", "text")
    return version


# 弹出确认框，询问用户是否重启
def confirm_restart(info):
    response = messagebox.askyesno(info, "是否确认重启程序？")
    if response:  # 如果选择是
        restart_program()

# 重启 Python 程序
def restart_program():
    python = sys.executable  # 获取当前 Python 解释器的路径
    os.execv(python, [python] + sys.argv)  # 重启程序

# 匹配带逗号的数字范围
def extract_number_range(text):
    match = re.search(r"(\d{1,3}(?:,\d{3})*) ~ (\d{1,3}(?:,\d{3})*)", text)
    if match:
        min_val, max_val = match.groups()
        # 移除逗号并转为整数
        min_num = int(min_val.replace(",", ""))
        max_num = int(max_val.replace(",", ""))
        return min_num, max_num
    return None

# int 10,000 转换 10000
def comma_str_to_int(number_string):
    number = int(number_string.replace(',', ''))
    return number

# 10000 转换为 10,000
def int_to_comma_str(number):
    number_string = "{:,}".format(number)
    return number_string

# 判断空文件
def is_file_empty(file_path):
    return os.path.getsize(file_path) == 0

# 加载 json 文件
def load_json(json_path):
    try:
        if is_file_empty(json_path): return {}

        with open(json_path, 'r', encoding='utf-8') as file:
            json_dir = json.load(file)
            return json_dir
    except Exception as e:
        error_msg = f"无法加载：{json_path}\n{e}"
        logger.error(error_msg)
        日志.error_queue_proc.error_queue.put(error_msg)
        return {}

# 根据字典，返回其值的列表
def get_dir_values_list(dir1):
    return list(dir1.values())

# 字典相加
def add_dicts(dict1, dict2):
    # 创建 dict1 的副本，以避免修改原始字典
    result = dict1.copy()
    # 更新 result 字典，以包含 dict2 中的键值对
    result.update(dict2)
    return result

# 判断字典的子字典全为空
def is_all_values_empty(dir1):
    return not any(dir1.values())

# 如果是 None 就转换为""
def output_string(value):
    return "" if value is None else value

# 判断一个字符串是否是字符串列表中某个字符串的子串
def is_substring(substring, string_list):
    return any(substring in s for s in string_list)

# 判断一个字符串是否是字符串列表中某个字符串的父串
def is_parentstring(parent_string, stringlist):
    if not parent_string or not stringlist:
        return False
    return any(s in parent_string for s in stringlist)

# 判断list1中的字符串是否是list2中某个字符串的父串
def list_val_in_another(list1, list2):
    for item in list1:
        if is_parentstring(item, list2):
            return True
        # else:
        #     return False
    return False

def list_is(list, string):
    return (len(list) == 1 and list[0] == string)

# 检查字典的键或值是否存在于指定列表中
def check_dict_in_list(input_dict, check_list, check_keys=True, check_values=True):
    if not input_dict: return False
    
    # 检查键
    if check_keys:
        for key in input_dict.keys():
            if key in check_list: return True
    
    # 检查值
    if check_values:
        for value in input_dict.values():
            if value.upper() in check_list: return True

    return False


# 检查目录是否存在，如果不存在则创建
def creat_directory(file_name):
    # 获取目录路径
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

# 计算需要填充的字节数量，使得总长度为8的倍数
def padding_data(data):
    padding_length = (8 - (len(data) % 8)) % 8
    padded_bytes = data + b'\x00' * padding_length
    return padded_bytes

# 整数转换为，字符串字节序列，十六进制，eg: 664572 => b"\x00\x00\x00a23fc"
def int_to_str_8bytes(value):
    hex_value = hex(value)[2:]
    hex_value_str_bytes = hex_value.encode('utf-8')
    hex_value_str_8bytes = hex_value_str_bytes.rjust(8, b'\x00')
    return hex_value_str_8bytes

#字符串字节序列，十六进制转换为整数，eg: b"\x00\x00\x00a23fc" => 664572
def str_8bytes_to_int(hex_value_str_8bytes):
    hex_value_str = hex_value_str_8bytes.decode('utf-8').lstrip('\x00')
    return int(hex_value_str, 16)

# 查找子字符串出现的全部位置，返回位置列表
def find_all_substring_positions(substring, string):
    start = 0
    positions = []
    while True:
        start = string.find(substring, start)
        if start == -1:  # substring not found
            break
        positions.append(start)
        start += len(substring)  # move to the position after the found substring
    return positions


# 将当前目录下的 webp logo 转换为 ico
def webp_to_ico(size=(80, 66)):

    # 获取当前目录下的所有文件
    for filename in os.listdir('.'):
        if filename.endswith('.webp'):
            # 构建完整的文件路径
            webppath = os.path.join('.', filename)
            # 加载图片
            iconimage = Image.open(webppath).convert("RGBA")
            # 调整图片大小
            iconimage = iconimage.resize(size, Image.LANCZOS)
            # 设置ICO文件路径
            tempiconpath = os.path.splitext(filename)[0] + '.ico'
            # 保存为ICO文件
            iconimage.save(tempiconpath, format='ICO', sizes=[(size[0], size[1])])

def delete_webp_files(directory: str) -> None:

    # if os.path.exists("./持有物/饰品/专武/Soul_png.png"):
    #     return

    # 检查目录是否存在
    if not os.path.exists(directory):
        return
    
    # 检查是否为有效目录
    if not os.path.isdir(directory):
        return
    
    # 转换为Path对象以便使用更现代的文件操作API
    dir_path = pathlib.Path(directory)
    
    # 遍历目录及其子目录中的所有.webp文件
    for webp_file in dir_path.rglob('*.webp'):
        # 构建同名PNG文件路径
        png_file = webp_file.with_suffix('.png')
        # 检查PNG文件是否存在
        if png_file.exists():
            try:
                # 删除文件
                webp_file.unlink()
            except PermissionError:
                logger.error(f"没有权限删除 {webp_file}")
                messagebox.showerror("错误", f"没有权限删除 {webp_file}")
            except Exception as e:
                logger.error(f"删除 {webp_file} 时出错: {e}")
                messagebox.showerror("错误", f"删除 {webp_file} 时出错: {e}")


def delete_mp3_files(directory: str) -> None:

    # 检查目录是否存在
    if not os.path.exists(directory):
        return
    
    # 检查是否为有效目录
    if not os.path.isdir(directory):
        return
    
    # 转换为Path对象以便使用更现代的文件操作API
    dir_path = pathlib.Path(directory)
    
    # 遍历目录及其子目录中的所有.mp3文件
    for mp3_file in dir_path.rglob('*.mp3'):
        # 构建同名flac文件路径
        flac_file = mp3_file.with_suffix('.flac')
        # 检查flac文件是否存在
        if flac_file.exists():
            try:
                # 删除文件
                mp3_file.unlink()
            except PermissionError:
                logger.error(f"没有权限删除 {mp3_file}")
                messagebox.showerror("错误", f"没有权限删除 {mp3_file}")
            except Exception as e:
                logger.error(f"删除 {mp3_file} 时出错: {e}")
                messagebox.showerror("错误", f"删除 {mp3_file} 时出错: {e}")

def delete_all_files_and_subdirs(directory):
    if not os.path.isdir(directory):
        return
    try:
        # 删除目录及其所有内容
        shutil.rmtree(directory)
        return True
    except Exception as e:
        logger.error(f"清空目录时发生错误: {e}")
        messagebox.showerror("错误", f"清空目录时发生错误: {e}")
        return False

def delete_old_file_and_subdirs():
    delete_webp_files("./")
    delete_mp3_files("./")
    delete_all_files_and_subdirs("./工具/HBRbrochure/chromedriver-win64")
    delete_all_files_and_subdirs("./工具/HBRbrochure/chrome_user_data")

def delete_file(file):
    if not os.path.isfile(file):
        return
    try:
        # 删除文件
        os.remove(file)
        return True
    except Exception as e:
        logger.error(f"删除文件时发生错误: {e}")
        messagebox.showerror("错误", f"删除文件时发生错误: {e}")
        return False



def read_txt_file(file_path: str, mode: str = 'text') -> str | list[str] | None:
    """
    读取txt文件内容，支持多种读取模式
    参数:
        file_path (str): 文件路径
        mode (str): 读取模式，可选值:
            - 'lines': 按行读取，返回字符串列表
            - 'text': 读取为字符串(默认)
            - 'binary': 以二进制模式读取
    返回:
        str | list[str] | None: 根据模式返回文件内容，失败时返回None
    """
    # 转换路径为绝对路径
    file_path = Path(file_path).absolute()
    
    # 检查文件是否存在
    if not file_path.exists():
        logger.error(f"文件不存在: {file_path}\n{e}")
        messagebox.showerror("错误", f"文件不存在: {file_path}\n{e}")
        return None
    
    # 检查是否为文件
    if not file_path.is_file():
        logger.error(f"不是有效的文件: {file_path}\n{e}")
        messagebox.showerror("错误", f"不是有效的文件: {file_path}\n{e}")
        return None
    
    # 检查文件是否可读
    if not os.access(file_path, os.R_OK):
        logger.error(f"文件不可读: {file_path}\n{e}")
        messagebox.showerror("错误", f"文件不可读: {file_path}\n{e}")
        return None
    
    try:
        if mode == 'binary':
            # 二进制模式读取
            with open(file_path, 'rb') as file:
                return file.read()
        elif mode == 'text':
            # 文本模式读取为单个字符串
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:  
            # 默认按行读取
            # 文本模式按行读取
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.readlines()
    except UnicodeDecodeError:
        logger.error(f"文件不是有效的UTF-8编码: {file_path}\n{e}")
        messagebox.showerror("错误", f"文件不是有效的UTF-8编码: {file_path}\n{e}")
        return None
    except Exception as e:
        logger.error(f"读取文件时发生意外错误: {file_path}\n{e}")
        messagebox.showerror("错误", f"读取文件时发生意外错误: {file_path}\n{e}")
        return None

def compute_hash(text, algorithm = "sha256"):

    # algorithm (str): 
    # md5
    # sha1
    # sha224, sha256, sha384, sha512 
    # sha3_224, sha3_256, sha3_384, sha3_512
    # blake2s 
    # crc32 非加密
    
    if algorithm == "crc32":
        return hex(binascii.crc32(text.encode('utf-8')))[2:]

    hash_func = hashlib.new(algorithm)
    hash_func.update(text.encode('utf-8'))
    return hash_func.hexdigest()

# bytes to hex str
def convert_hex_escape_to_string(hex_escape_string):
    # 使用正则表达式匹配\x后跟两个十六进制字符的模式
    hex_pattern = r'\\x([0-9a-fA-F]{2})'
    
    # 查找所有匹配项
    matches = re.findall(hex_pattern, hex_escape_string)
    
    # 将匹配到的十六进制值连接成字符串
    result = ''.join(matches)
    
    return result

# hex to bytes str
def convert_hex_string_to_escape(hex_string):
    # 确保输入是有效的十六进制字符串（只包含0-9和a-f或A-F）
    if not re.match(r'^[0-9a-fA-F]+$', hex_string):
        logger.error("输入必须是有效的十六进制字符串")
        raise ValueError("输入必须是有效的十六进制字符串")
    
    # 确保十六进制字符串长度是偶数
    if len(hex_string) % 2 != 0:
        logger.error("十六进制字符串长度必须是偶数")
        raise ValueError("十六进制字符串长度必须是偶数")
    
    # 将每两个字符作为一组，转换为\xHH格式
    result = ''
    for i in range(0, len(hex_string), 2):
        byte = hex_string[i:i+2]
        result += f'\\x{byte}'
    
    return result

# 返回列表不是数字元素的第一个下标
def get_list_not_isinstance_index(a):
    index = None
    for index, item in enumerate(a):
        if not isinstance(item, (int, float)):
            return index

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
def init_chrome_driver(chrome_options):

    # 设置 ChromeDriver 的服务，初始化 Chrome WebDriver
    try:
        chromedriver_path = "./工具/chrome/chromedriver-win64/chromedriver.exe"
        service = Service(executable_path=chromedriver_path)
        
    except Exception as e:
        logger.info("进入 ChromeDriverManager 模式\n需要等待自动安装")
        messagebox.showinfo("信息", f"进入 ChromeDriverManager 模式\n需要等待自动安装")
        service = Service(executable_path=ChromeDriverManager().install())

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        if "chrome not found" in str(e).lower():
            logger.error("Chrome 未安装或路径不正确！")
            messagebox.showerror("错误", "Chrome 未安装或路径不正确！")
            return None
        else:
            logger.error(f"浏览器启动失败: {str(e)}")
            messagebox.showerror("错误", f"浏览器启动失败: {str(e)}")
            return None

    return driver


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_admin():
    if not is_admin():
        # 重新以管理员权限运行脚本
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

def format_hex_dump(hex_string, bytes_per_line=16):
    
    # 格式化十六进制输出
    result = []
    
    # 将十六进制字符串分组，每2个字符代表一个字节
    hex_bytes = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]
    
    for i in range(0, len(hex_bytes), bytes_per_line):
        # 当前行的字节
        line_bytes = hex_bytes[i:i+bytes_per_line]
        
        # 偏移量
        offset = f"{i:08x}"
        
        # 十六进制部分
        hex_part = ' '.join(f"{b:>2s}" for b in line_bytes)
        # 填充不足的部分
        hex_part += '   ' * (bytes_per_line - len(line_bytes))
        
        ascii_part = ''
        for b in line_bytes:
            byte_val = int(b, 16)
            if 32 <= byte_val <= 126:  # 可打印ASCII字符
                ascii_part += chr(byte_val)
            else:
                ascii_part += '.'
        
        result.append(f"{offset}  {hex_part}  |{ascii_part}|")
    
    return '\n'.join(result)

def not_letter(text):
    return not any(char.isalpha() for char in text) 
