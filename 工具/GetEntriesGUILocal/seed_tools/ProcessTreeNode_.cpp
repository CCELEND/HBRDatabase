#include "ProcessTreeNode_.h"

// 创建进程树节点
ProcessTreeNode* create_process_node(DWORD pid)
{
    ProcessTreeNode* node = (ProcessTreeNode*)malloc(sizeof(ProcessTreeNode));
    if (node) {
        node->pid = pid;
        node->children = NULL;
        node->child_count = 0;
    }
    return node;
}

// 创建扩展进程节点
ProcessTreeNodeEx* create_process_node_ex(DWORD pid) 
{
    ProcessTreeNodeEx* node = (ProcessTreeNodeEx*)malloc(sizeof(ProcessTreeNodeEx));
    if (node) {
        node->pid = pid;
        node->children = NULL;
        node->child_count = 0;
        node->thread_ids = NULL;
        node->original_suspend_counts = NULL;
        node->thread_count = 0;
    }
    return node;
}