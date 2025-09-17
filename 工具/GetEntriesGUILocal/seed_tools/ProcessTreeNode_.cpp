#include "ProcessTreeNode_.h"

// �����������ڵ�
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

// ������չ���̽ڵ�
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