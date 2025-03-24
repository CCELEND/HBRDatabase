
from hash import calculate_file_hashes, save_hashes_to_json
from tools import load_json, is_all_values_empty

from client import send_hashes_to_server
import asyncio
import json


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

