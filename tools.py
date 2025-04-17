import sys
import os
from PIL import Image, ImageTk
from tkinter import messagebox
import json
import subprocess
import importlib
import re

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

# 判断空文件
def is_file_empty(file_path):
    return os.path.getsize(file_path) == 0

# 加载 json 文件
def load_json(json_path):
    try:
        if is_file_empty(json_path):
            return {}

        with open(json_path, 'r', encoding='utf-8') as file:
            json_dir = json.load(file)
            return json_dir
    except Exception as e:
        messagebox.showerror("错误", f"无法加载：{json_path}\n{e}")

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