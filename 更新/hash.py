
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import json


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

    # 遍历目录，收集所有需要计算哈希的文件路径
    file_tasks = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            # 使用相对路径作为键，格式为 "./目录名/子目录/文件名"
            key = os.path.join('.', os.path.relpath(filepath, start=os.path.dirname(directory)))

            # 跳过不需要的文件
            if "__pycache__" in key or "local_file_hash.json" in key:
                continue

            # 将反斜杠替换为正斜杠
            if '\\' in key:
                key = key.replace('\\', '/')

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
                print(f"计算文件：{key}的哈希值时出错：{e}")

    return file_hashes

