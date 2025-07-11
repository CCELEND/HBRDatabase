
import os
import hashlib
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

"""
比较两个哈希字典，返回差异字典
:param dict1: 第一个哈希字典
:param dict2: 第二个哈希字典
:return: 差异字典，包含新增、删除和修改的键
"""
def compare_hashes(dict1, dict2):

    diff_dict = {
        'added': {},   # 新增的键
        'deleted': {}, # 删除的键
        'modified': {} # 修改的键
    }

    # 获取所有键的集合
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())

    # 查找新增的键
    added_keys = keys2 - keys1
    for key in added_keys:
        diff_dict['added'][key] = dict2[key]

    # 查找删除的键
    deleted_keys = keys1 - keys2
    for key in deleted_keys:
        diff_dict['deleted'][key] = dict1[key]

    # 查找修改的键
    common_keys = keys1 & keys2
    for key in common_keys:
        if dict1[key] != dict2[key]:
            diff_dict['modified'][key] = {
                'old_value': dict1[key],
                'new_value': dict2[key]
            }

    return diff_dict

# 保存为 json 文件
def save_hashes_to_json(file_hashes, json_file_path):
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(file_hashes, json_file, indent=4, ensure_ascii=False)

# 计算单个文件的哈希值
def calculate_file_hash(filepath, key):
    with open(filepath, 'rb') as f:
        file_content = f.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
    return key, file_hash

# 计算单个文件的哈希值（分块读取）
def calculate_file_hash_block(filepath, key):   
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return key, sha256_hash.hexdigest()

# 计算指定目录下所有文件的哈希值（使用多线程）
def calculate_file_hashes(directory):
    file_hashes = {}
    skip_items = ["__pycache__", ".mp3", ".flac", ".xlsx", "chrome_user_data"]

    # 遍历目录，收集所有需要计算哈希的文件路径
    file_tasks = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            # 使用相对路径作为键，格式为 "./目录名/子目录/文件名"
            key = os.path.join('.', os.path.relpath(filepath, start=os.path.dirname(directory)))

            # 将反斜杠替换为正斜杠
            if '\\' in key:
                key = key.replace('\\', '/')

            # 跳过不需要的文件
            if any(item in key for item in skip_items):
                continue

            # 将任务添加到任务列表
            file_tasks.append((filepath, key))

    # 使用 ThreadPoolExecutor 并行计算哈希
    with ThreadPoolExecutor() as executor:
        # 提交任务到线程池
        futures = {executor.submit(calculate_file_hash, filepath, key): key for filepath, key in file_tasks}

        # 等待任务完成并收集结果
        for future in as_completed(futures):
            key = futures[future]
            try:
                key, file_hash = future.result()
                file_hashes[key] = file_hash
            except Exception as e:
                messagebox.showerror("错误", f"计算文件：{key}的哈希值时出错：{e}")

    return file_hashes

