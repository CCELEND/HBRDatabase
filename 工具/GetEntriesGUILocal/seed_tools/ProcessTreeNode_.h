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

// �߳���س���
constexpr DWORD MAX_THREADS_PER_PROCESS = 1024; // �����������֧���߳���


// �������ڵ�ṹ
typedef struct ProcessTreeNode {
    DWORD pid;
    struct ProcessTreeNode** children;
    size_t child_count;
} ProcessTreeNode;


// ��չ��Ľ������ڵ㣨�����߳���Ϣ�洢��
typedef struct ProcessTreeNodeEx {
    DWORD pid;
    struct ProcessTreeNodeEx** children;
    size_t child_count;
    DWORD* thread_ids;         // �ý��̵������߳�ID
    DWORD* original_suspend_counts; // ÿ���̵߳�ԭ�������
    DWORD thread_count;        // �߳�����
} ProcessTreeNodeEx;

ProcessTreeNode* create_process_node(DWORD pid);
ProcessTreeNodeEx* create_process_node_ex(DWORD pid);
