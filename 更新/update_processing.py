
from hash import calculate_file_hashes, save_hashes_to_json
from tools import load_json, is_all_values_empty

from client import send_hashes_to_server
import asyncio
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

def update_data():

    # local_file_hashes_path = "./更新/local_file_hash.json"
    current_file_hashes = calculate_file_hashes("./")

    # local_file_hashes = load_json(local_file_hashes_path)
    # ini_local_file_hash_flag = False
    # if not local_file_hashes:
    #     save_hashes_to_json(current_file_hashes, local_file_hashes_path)
    #     local_file_hashes = current_file_hashes.copy()
    #     ini_local_file_hash_flag = True

    # # 比较两个哈希字典
    # diff = compare_hashes(local_file_hashes, current_file_hashes)
    # if is_all_values_empty(diff) and not ini_local_file_hash_flag:
    #     return

    # current_file_hashes 发送给服务器
    asyncio.run(send_hashes_to_server(current_file_hashes))

    # current_file_hashes = calculate_file_hashes("./")
    # save_hashes_to_json(current_file_hashes, local_file_hashes_path)

