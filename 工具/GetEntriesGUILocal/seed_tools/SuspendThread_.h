#pragma once

# include "ProcessTreeNode_.h"

// ����ָ��PID�������̣߳���ȡ�߳�ID�б�
static DWORD enum_process_threads(DWORD pid, DWORD* threads, DWORD max_threads);

// ��ͣ�����̣߳�����¼ԭ�������
static BOOL suspend_single_thread(DWORD tid, DWORD* original_suspend_count);

// �ָ������̵߳���ͣǰ�Ĺ������״̬
static BOOL resume_single_thread(DWORD tid, DWORD original_suspend_count);

// ������չ�������ڵ�
static ProcessTreeNodeEx* create_process_node_ex(DWORD pid);

// �ݹ鹹��������
ProcessTreeNodeEx* build_process_tree_ex(DWORD root_pid);

// �ݹ���ͣ�����������н��̵������߳�
BOOL suspend_process_tree_ex(ProcessTreeNodeEx* node);

// �ݹ�ָ������������н��̵������߳�
BOOL resume_process_tree_ex(ProcessTreeNodeEx* node);

// �ݹ��ͷ���չ������
void free_process_tree_ex(ProcessTreeNodeEx* node);
