#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


import math
import concurrent.futures

from 工具.GetEntriesGUILocal.get_ct import get_random_value, get_property
from 工具.GetEntriesGUILocal.get_ct import career_entry, charm_entry, wash_entry
from 工具.GetEntriesGUILocal.get_ct import spct

def list_dict(dict):
    keys = list(dict.keys())
    ranges = list(dict.values())
    return keys, ranges


def wash_process_index(seed, cur_index):
    # 处理单个索引的核心函数
    real = get_random_value(seed, cur_index)
    wash_entry_str = get_property(real, wash_entry)
    return str(cur_index), [wash_entry_str, str(real)]

def equipment_process_index(seed, cur_index):
    real = get_random_value(seed, cur_index)
    spct_str = get_property(real, spct)
    career_entry_str = get_property(real, career_entry)
    charm_entry_str = get_property(real, charm_entry)
    spct_list = spct_str.split()
    return str(cur_index), spct_list+["自选属性"]+[career_entry_str+"的初始SP+3", charm_entry_str, str(real)]

def parallel_process_indexes(fun, seed, start_index, end_index, 
                          chunk_size=10, max_workers=None):

    index_wash_entries = {}
    total_tasks = end_index - start_index
    
    # 计算合理的chunk_size(至少处理10个索引/任务)
    chunk_size = max(chunk_size, 10)
    num_chunks = math.ceil(total_tasks / chunk_size)
    
    # 创建任务列表(每个任务处理一个chunk)
    chunks = [
        range(
            start_index + i * chunk_size,
            min(start_index + (i + 1) * chunk_size, end_index)
        )
        for i in range(num_chunks)
    ]
    
    # 使用进程池并行处理
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有chunk任务
        future_to_chunk = {
            executor.submit(process_chunk, fun, seed, chunk): chunk
            for chunk in chunks
        }
        
        # 获取并合并结果
        for future in concurrent.futures.as_completed(future_to_chunk):
            try:
                chunk_result = future.result()
                index_wash_entries.update(chunk_result)
            except Exception as e:
                print(f"Error processing chunk: {e}")
    
    return index_wash_entries

def process_chunk(fun, seed, chunk_indices):
    if fun == 0:
        # 处理一个索引块
        return dict(wash_process_index(seed, i) for i in chunk_indices)
    else:
        return dict(equipment_process_index(seed, i) for i in chunk_indices)
