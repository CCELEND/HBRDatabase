#pragma once

# include "ProcessTreeNode_.h"

// 遍历指定PID的所有线程，获取线程ID列表
static DWORD enum_process_threads(DWORD pid, DWORD* threads, DWORD max_threads);

// 暂停单个线程，并记录原挂起计数
static BOOL suspend_single_thread(DWORD tid, DWORD* original_suspend_count);

// 恢复单个线程到暂停前的挂起计数状态
static BOOL resume_single_thread(DWORD tid, DWORD original_suspend_count);

// 创建扩展进程树节点
static ProcessTreeNodeEx* create_process_node_ex(DWORD pid);

// 递归构建进程树
ProcessTreeNodeEx* build_process_tree_ex(DWORD root_pid);

// 递归暂停进程树中所有进程的所有线程
BOOL suspend_process_tree_ex(ProcessTreeNodeEx* node);

// 递归恢复进程树中所有进程的所有线程
BOOL resume_process_tree_ex(ProcessTreeNodeEx* node);

// 递归释放扩展进程树
void free_process_tree_ex(ProcessTreeNodeEx* node);
