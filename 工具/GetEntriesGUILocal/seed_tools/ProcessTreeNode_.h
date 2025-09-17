#pragma once
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <psapi.h>


constexpr size_t BUFFER_SIZE = 4096;
constexpr size_t MAX_PID_LEN = 16;
const uint64_t SEARCH_START = 0x10000000000;
const uint64_t SEARCH_END = 0x30000000000;

// 线程相关常量
constexpr DWORD MAX_THREADS_PER_PROCESS = 1024; // 单个进程最大支持线程数


// 进程树节点结构
typedef struct ProcessTreeNode {
    DWORD pid;
    struct ProcessTreeNode** children;
    size_t child_count;
} ProcessTreeNode;


// 扩展后的进程树节点（增加线程信息存储）
typedef struct ProcessTreeNodeEx {
    DWORD pid;
    struct ProcessTreeNodeEx** children;
    size_t child_count;
    DWORD* thread_ids;         // 该进程的所有线程ID
    DWORD* original_suspend_counts; // 每个线程的原挂起计数
    DWORD thread_count;        // 线程数量
} ProcessTreeNodeEx;

ProcessTreeNode* create_process_node(DWORD pid);
ProcessTreeNodeEx* create_process_node_ex(DWORD pid);
