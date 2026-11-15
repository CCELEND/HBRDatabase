
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from 日志.advanced_logger import AdvancedLogger
from 更新.local_policy import HASH_SKIP_DIRS, is_local_only_path
logger = AdvancedLogger.get_logger(__name__)

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

# 本地哈希缓存：记录每个文件的 mtime/size/hash，没变的文件直接复用，
# 避免每次启动都把整套资源（约 1.5GB）重新 SHA-256 一遍。
# 文件名已在 skip_items 里，不会被当成待哈希文件。
CLIENT_HASH_CACHE = "./关于/client_file_hashes.json"


def _load_hash_cache():
    try:
        with open(CLIENT_HASH_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_hash_cache(cache):
    try:
        directory = os.path.dirname(CLIENT_HASH_CACHE)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(CLIENT_HASH_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning("写入本地哈希缓存失败：%s", e)


def calculate_file_hashes(directory, use_cache=True):
    file_hashes = {}
    cache = _load_hash_cache() if use_cache else {}
    new_cache = {}
    reused = 0

    # 遍历目录，能复用缓存的直接取，其余加入待计算列表
    file_tasks = []
    for root, dirs, files in os.walk(directory):
        # 剪枝：不进入 venv/.git/.vs 等目录
        dirs[:] = [d for d in dirs if d not in HASH_SKIP_DIRS]
        for filename in files:
            filepath = os.path.join(root, filename)
            # 使用相对路径作为键，格式为 "./目录名/子目录/文件名"
            key = os.path.join('.', os.path.relpath(filepath, start=os.path.dirname(directory)))

            # 将反斜杠替换为正斜杠
            if '\\' in key:
                key = key.replace('\\', '/')

            # 本地配置、日志、下载资源、运行时解压目录等不参与哈希。
            if is_local_only_path(key):
                continue

            try:
                st = os.stat(filepath)
            except OSError:
                continue

            entry = cache.get(key)
            if (isinstance(entry, dict) and entry.get("hash")
                    and entry.get("mtime") == st.st_mtime
                    and entry.get("size") == st.st_size):
                file_hashes[key] = entry["hash"]
                new_cache[key] = entry
                reused += 1
            else:
                file_tasks.append((filepath, key, st.st_mtime, st.st_size))

    # 使用 ThreadPoolExecutor 并行计算「缓存未命中」的文件
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(calculate_file_hash, filepath, key):
                (key, mtime, size)
            for filepath, key, mtime, size in file_tasks
        }

        # 等待任务完成并收集结果
        for future in as_completed(futures):
            key, mtime, size = futures[future]
            try:
                result_key, file_hash = future.result()
                if result_key is not None:
                    file_hashes[result_key] = file_hash
                    new_cache[result_key] = {
                        "mtime": mtime, "size": size, "hash": file_hash}
            except FileNotFoundError as e:
                # 文件在遍历后被删除/移动，直接跳过，不再弹窗
                logger.warning(f"文件已被删除或移动，跳过哈希计算：{key} ({e})")
            except (PermissionError, OSError) as e:
                logger.error(f"计算文件 {key} 的哈希值时出错：{e}")

    if use_cache:
        _save_hash_cache(new_cache)
        # logger.info("哈希完成：复用缓存 %d 个，重新计算 %d 个",
        #             reused, len(file_tasks))

    return file_hashes