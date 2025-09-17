# include "SuspendThread_.h"

/**
 * @brief ����ָ��PID�������̣߳���ȡ�߳�ID�б�
 * @param pid Ŀ�����ID
 * @param threads ����������洢�߳�ID������
 * @param max_threads �����������������Խ�磩
 * @return ʵ�ʻ�ȡ���߳�������0��ʾʧ��
 */
static DWORD enum_process_threads(DWORD pid, DWORD* threads, DWORD max_threads) {
    // ���У�飬��������ֱ�ӷ���
    if (pid == 0 || threads == NULL || max_threads == 0) {
        fprintf(stderr, "    [-] Invalid parameter for enum_process_threads\n");
        return 0;
    }

    // �����߳̿��գ�ʧ����ֱ�ӷ���
    HANDLE hThreadSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (hThreadSnapshot == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "    [-] CreateToolhelp32Snapshot (thread) failed (PID: %d, Error: %lu)\n",
            pid, GetLastError());
        return 0;
    }

    THREADENTRY32 thread_entry = { 0 };
    thread_entry.dwSize = sizeof(THREADENTRY32); // ��ʼ���ṹ���С
    DWORD thread_count = 0;

    // ���Ի�ȡ��һ���߳���Ϣ��ʧ�����ͷ���Դ������
    if (!Thread32First(hThreadSnapshot, &thread_entry)) {
        fprintf(stderr, "    [-] Thread32First failed (PID: %d, Error: %lu)\n",
            pid, GetLastError());
        CloseHandle(hThreadSnapshot);
        return 0;
    }

    // ���������߳�
    do {
        // ɸѡĿ����̵��߳�
        if (thread_entry.th32OwnerProcessID != pid) continue;


        // ����Ƿ񳬳�����߳�������
        if (thread_count >= max_threads) {
            fprintf(stderr, "    [-] Too many threads (PID: %d, max: %lu), skip remaining\n",
                pid, max_threads);
            break;
        }

        // ��¼�߳�ID
        threads[thread_count++] = thread_entry.th32ThreadID;

    } while (Thread32Next(hThreadSnapshot, &thread_entry));

    // �ͷ���Դ�����ؽ��
    CloseHandle(hThreadSnapshot);
    return thread_count;
}


/**
 * @brief ��ͣ�����̣߳�����¼ԭ�������
 * @param tid Ŀ���߳�ID
 * @param original_suspend_count ����������洢�߳���ͣǰ�Ĺ������
 * @return TRUE����ͣ�ɹ���FALSE��ʧ��
 */
static BOOL suspend_single_thread(DWORD tid, DWORD* original_suspend_count) {
    if (tid == 0 || original_suspend_count == NULL) {
        fprintf(stderr, "    [-] Invalid parameter for suspend_single_thread\n");
        return FALSE;
    }

    // ���̣߳��� THREAD_SUSPEND_RESUME����ͣ/�ָ�Ȩ�ޣ��� THREAD_QUERY_INFORMATION����ȡ�������Ȩ�ޣ�
    HANDLE hThread = OpenThread(
        THREAD_SUSPEND_RESUME | THREAD_QUERY_INFORMATION,
        FALSE, // ���̳о��
        tid
    );
    if (hThread == NULL) {
        fprintf(stderr, "    [-] OpenThread failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        return FALSE;
    }

    // ��ͣ�̣߳�SuspendThread ���ز���ǰ�Ĺ��������0��ʾδ����n��ʾ�ѱ�����n�Σ�
    DWORD suspend_count = SuspendThread(hThread);
    if (suspend_count == (DWORD)-1) { // ʧ�ܷ��� -1����0xFFFFFFFF��
        fprintf(stderr, "    [-] SuspendThread failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        CloseHandle(hThread);
        return FALSE;
    }

    // ��¼ԭ��������������ָ�ʱ�軹ԭ����ֵ��
    *original_suspend_count = suspend_count;
    //printf("        [+] Suspended thread (TID: %lu) | Original suspend count: %lu\n",
    //    tid, suspend_count);

    CloseHandle(hThread); // �ͷ��߳̾��
    return TRUE;
}


/**
 * @brief �ָ������̵߳���ͣǰ�Ĺ������״̬
 * @param tid Ŀ���߳�ID
 * @param original_suspend_count �߳���ͣǰ�Ĺ���������� suspend_single_thread ��¼��
 * @return TRUE���ָ��ɹ���FALSE��ʧ��
 */
static BOOL resume_single_thread(DWORD tid, DWORD original_suspend_count) {
    if (tid == 0) {
        fprintf(stderr, "    [-] Invalid parameter for resume_single_thread\n");
        return FALSE;
    }

    HANDLE hThread = OpenThread(
        THREAD_SUSPEND_RESUME | THREAD_QUERY_INFORMATION,
        FALSE,
        tid
    );
    if (hThread == NULL) {
        fprintf(stderr, "    [-] OpenThread failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        return FALSE;
    }

    // ����1����ȡ��ǰ�̵߳Ĺ��������������ͣһ�λ�ȡ���ٳ����ô���ͣ��
    DWORD current_suspend_count = SuspendThread(hThread); // ��ͣһ�Σ����ز���ǰ�ļ���
    if (current_suspend_count == (DWORD)-1) {
        fprintf(stderr, "    [-] Get suspend count failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        CloseHandle(hThread);
        return FALSE;
    }
    ResumeThread(hThread); // �����ղŵ���ͣ���ָ�������ǰ�ļ���

    // ������Ҫ�ָ��Ĵ�������ǰ������� - ԭ���������
    DWORD need_resume_count = current_suspend_count - original_suspend_count;
    if (need_resume_count > 0) {
        for (DWORD i = 0; i < need_resume_count; i++) {
            ResumeThread(hThread); // ÿ�ε��ü���1���������
        }
        //printf("        [+] Resumed thread (TID: %lu) | Restored suspend count: %lu\n",
        //    tid, original_suspend_count);
    }
    //else {
    //    printf("        [+] Thread (TID: %lu) already in original state | Suspend count: %lu\n",
    //        tid, original_suspend_count);
    //}

    CloseHandle(hThread);
    return TRUE;
}


/**
 * @brief ������չ�������ڵ㣨���߳���Ϣ�洢��
 * @param pid Ŀ�����ID
 * @return �ڵ�ָ�룺�ɹ����ط�NULL��ʧ�ܷ���NULL
 */
static ProcessTreeNodeEx* create_process_node_ex(DWORD pid) {
    ProcessTreeNodeEx* node = (ProcessTreeNodeEx*)malloc(sizeof(ProcessTreeNodeEx));
    if (node == NULL) {
        fprintf(stderr, "    [-] Malloc ProcessTreeNodeEx failed (PID: %d)\n", pid);
        return NULL;
    }

    // ��ʼ���ڵ��Ա
    node->pid = pid;
    node->children = NULL;
    node->child_count = 0;
    node->thread_ids = NULL;
    node->original_suspend_counts = NULL;
    node->thread_count = 0;

    return node;
}

/**
 * @brief �ݹ��ͷ���չ�����������߳���Ϣ��
 * @param node ���������ڵ�
 */
void free_process_tree_ex(ProcessTreeNodeEx* node) {
    if (node == NULL) return;

    // �ݹ��ͷ������ӽڵ�
    for (size_t i = 0; i < node->child_count; i++) {
        free_process_tree_ex(node->children[i]);
    }
    free(node->children); // �ͷ��ӽڵ�����

    // �ͷ��߳���Ϣ����
    free(node->thread_ids);
    free(node->original_suspend_counts);

    free(node); // �ͷŵ�ǰ�ڵ�
}


/**
 * @brief �ݹ鹹������������ÿ�����̵��߳���Ϣ��
 * @param root_pid ���������ڵ�PID��Ŀ��������PID��
 * @return ���������ڵ�ָ�룺�ɹ����ط�NULL��ʧ�ܷ���NULL
 */
ProcessTreeNodeEx* build_process_tree_ex(DWORD root_pid) {
    // ������ǰ���̽ڵ㣨��ǰ������Ч�ڵ㣩
    ProcessTreeNodeEx* root_node = create_process_node_ex(root_pid);
    if (root_node == NULL) {
        fprintf(stderr, "    [-] Create root node failed (PID: %d)\n", root_pid);
        return NULL;
    }

    // Ϊ��ǰ�ڵ��ȡ����ʼ���߳���Ϣ
    DWORD threads[MAX_THREADS_PER_PROCESS] = { 0 };
    DWORD thread_count = enum_process_threads(root_pid, threads, MAX_THREADS_PER_PROCESS);

    // �����߳��� > 0 ʱ���ŷ����ڴ�洢�߳���Ϣ
    if (thread_count > 0) {
        // �����߳�ID�͹���������飨����������ͬʱ�ɹ��������ͷ��ѷ�����Դ��
        root_node->thread_ids = (DWORD*)malloc(thread_count * sizeof(DWORD));
        root_node->original_suspend_counts = (DWORD*)malloc(thread_count * sizeof(DWORD));

        // �ڴ����ʧ�ܣ��ͷ������ѷ�����Դ������NULL
        if (root_node->thread_ids == NULL || root_node->original_suspend_counts == NULL) {
            fprintf(stderr, "    [-] Malloc thread info failed (PID: %d)\n", root_pid);
            free(root_node->thread_ids);    // ��ʹΪNULL��freeҲ��ȫ
            free(root_node->original_suspend_counts);
            free_process_tree_ex(root_node); // �ͷ��������ڵ�
            return NULL;
        }

        // �����߳�ID���ڵ㣬��ʼ���߳���
        memcpy(root_node->thread_ids, threads, thread_count * sizeof(DWORD));
        root_node->thread_count = thread_count;
        //printf("    [+] Process (PID: %d) has %lu threads\n", root_pid, thread_count);
    }
    //else {
    //    // �߳���Ϊ0��ö��ʧ�ܻ����̣߳�����������ڴ�
    //    printf("    [+] Process (PID: %d) has no threads (or enum failed)\n", root_pid);
    //}

    // �������̿��գ�ʧ����������ڵ㲢���أ�
    HANDLE hProcessSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hProcessSnapshot == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "    [-] Create process snapshot failed (PID: %d, Error: %lu)\n",
            root_pid, GetLastError());
        free_process_tree_ex(root_node); // �����Ѵ����ĸ��ڵ�
        return NULL;
    }

    // ����ϵͳ���̣��ݹ鹹���ӽ�����
    PROCESSENTRY32 process_entry = { 0 };
    process_entry.dwSize = sizeof(PROCESSENTRY32); // ��ʼ���ṹ���С

    // ���Ի�ȡ��һ��������Ϣ��ʧ����������պ͸��ڵ�
    if (!Process32First(hProcessSnapshot, &process_entry)) {
        fprintf(stderr, "    [-] Process32First failed (PID: %d, Error: %lu)\n",
            root_pid, GetLastError());
        CloseHandle(hProcessSnapshot);   // �ͷſ��վ��
        free_process_tree_ex(root_node); // ������ڵ�
        return NULL;
    }

    // �������н���
    do {
        // ��������ǰ���̲��Ǹ��ڵ���ӽ��̣���PID��ƥ�䣩
        if (process_entry.th32ParentProcessID != root_pid) continue;

        // �ݹ鴴���ӽ��̽ڵ㣨���ӽ��̵��߳���Ϣ��
        ProcessTreeNodeEx* child_node = build_process_tree_ex(process_entry.th32ProcessID);
        // �������ӽڵ㴴��ʧ�ܣ����账������������һ�����̣�
        if (child_node == NULL) {
            fprintf(stderr, "    [-] Create child node failed (Child PID: %d, Parent PID: %d)\n",
                process_entry.th32ProcessID, root_pid);
            continue;
        }

        // ��չ�ӽ������飨realloc ���·����ڴ棩
        ProcessTreeNodeEx** new_children = (ProcessTreeNodeEx**)realloc(
            root_node->children,
            (root_node->child_count + 1) * sizeof(ProcessTreeNodeEx*)
        );
        // �ڴ����ʧ�ܣ��ͷŵ�ǰ�ӽڵ㣬������������Ӱ�������ӽ��̣�
        if (new_children == NULL) {
            fprintf(stderr, "    [-] Realloc child array failed (Child PID: %d, Parent PID: %d)\n",
                process_entry.th32ProcessID, root_pid);
            free_process_tree_ex(child_node);
            continue;
        }

        // �ɹ�����ӽڵ㵽���ڵ�
        root_node->children = new_children;
        root_node->children[root_node->child_count++] = child_node;
        //printf("    [+] Added child process (PID: %d) to parent (PID: %d)\n",
        //    process_entry.th32ProcessID, root_pid);

    } while (Process32Next(hProcessSnapshot, &process_entry));

    // ������Դ�����ظ��ڵ�
    CloseHandle(hProcessSnapshot); // �ͷŽ��̿��վ��
    return root_node;
}



/**
 * @brief �ݹ���ͣ�����������н��̵������߳�
 * @param node �������ڵ㣨��ǰҪ����Ľ��̣�
 * @return BOOL��TRUE��ʾ��ǰ�ڵ㼰�ӽڵ����ͣ������ִ�У���ʹ�����߳�ʧ�ܣ���FALSE��ʾ�ڵ���Ч
 * @note ��ͣ˳���ȵݹ���ͣ�����ӽ��� �� ����ͣ��ǰ���̵��̣߳������ӽ��̱������̻��ѣ�
 */
BOOL suspend_process_tree_ex(ProcessTreeNodeEx* node) {
    // �߽��飺�ڵ�Ϊ��ֱ�ӷ���
    if (node == NULL) {
        fprintf(stderr, "    [-] Invalid ProcessTreeNodeEx (NULL) in suspend_process_tree_ex\n");
        return FALSE;
    }

    BOOL is_operation_executed = TRUE; // ����Ƿ�ִ������ͣ��������ʹ�����߳�ʧ�ܣ�
    //printf("\n    [*] Starting to suspend process tree node: PID = %d\n", node->pid);

    // �ݹ���ͣ�����ӽ���
    if (node->child_count > 0) {
        //printf("    [*] Found %zu child processes for PID %d, suspending children first...\n",
        //    node->child_count, node->pid);

        for (size_t i = 0; i < node->child_count; i++) 
        {
            ProcessTreeNodeEx* child_node = node->children[i];
            if (child_node == NULL) {
                fprintf(stderr, "    [-] Skip NULL child node of PID %d (index: %zu)\n",
                    node->pid, i);
                continue;
            }

            // �ݹ���ã���ͣ�ӽ��̵��߳���
            //printf("    [*] Entering child process: PID = %d (parent PID: %d)\n",
            //    child_node->pid, node->pid);
            if (!suspend_process_tree_ex(child_node)) {
                fprintf(stderr, "    [-] Failed to execute suspend for child PID %d (parent PID: %d)\n",
                    child_node->pid, node->pid);
                is_operation_executed = FALSE; // �ӽ�����ͣ����ִ��ʧ�ܣ��������״̬
            }
            //else {
            //    printf("    [+] Completed suspending child process: PID = %d (parent PID: %d)\n",
            //        child_node->pid, node->pid);
            //}
        }
    }
    //else {
    //    printf("    [*] No child processes for PID %d, skip child suspension\n", node->pid);
    //}

    // ��ͣ��ǰ���̵������߳�
    if (node->thread_count == 0) {
        //printf("    [*] No threads found for PID %d, skip thread suspension\n", node->pid);
        return is_operation_executed;
    }
    if (node->thread_ids == NULL || node->original_suspend_counts == NULL) {
        fprintf(stderr, "    [-] Thread info (IDs/counts) is NULL for PID %d, cannot suspend threads\n",
            node->pid);
        is_operation_executed = FALSE;
        return is_operation_executed;
    }

    //printf("    [*] Starting to suspend %lu threads of PID %d...\n",
    //    node->thread_count, node->pid);

    DWORD success_count = 0; // ͳ�Ƴɹ���ͣ���߳���
    for (DWORD i = 0; i < node->thread_count; i++) {
        DWORD tid = node->thread_ids[i];
        // ���ù��ߺ�����ͣ�����̣߳�����¼ԭ����������ڵ�� original_suspend_counts ����
        if (suspend_single_thread(tid, &(node->original_suspend_counts[i]))) {
            success_count++;
        }
        else {
            fprintf(stderr, "    [-] Suspending thread (TID: %lu) of PID %d failed (index: %lu)\n",
                tid, node->pid, i);
        }
    }

    // �����ǰ���̵���ͣ���ͳ��
    if (success_count == node->thread_count) {
        //printf("    [+] Successfully suspended ALL %lu threads of PID %d\n",
        //    node->thread_count, node->pid);
    }
    else if (success_count > 0) {
        printf("    [!] Partially suspended threads of PID %d: %lu success, %lu failed\n",
            node->pid, success_count, node->thread_count - success_count);
        is_operation_executed = FALSE; // ����ʧ�ܣ��������״̬
    }
    else {
        fprintf(stderr, "    [-] FAILED to suspend ANY threads of PID %d\n", node->pid);
        is_operation_executed = FALSE;
    }

    return is_operation_executed;
}

/**
 * @brief �ݹ�ָ������������н��̵������߳�
 * @param node �������ڵ㣨��ǰҪ����Ľ��̣�
 * @return BOOL��TRUE��ʾ�ָ�������ִ�У���ʹ�����߳�ʧ�ܣ���FALSE��ʾ�ڵ���Ч
 * @note �ָ�˳���Ȼָ���ǰ���̵��߳� �� �ٵݹ�ָ������ӽ��̣�����ͣ˳���෴��
 */
BOOL resume_process_tree_ex(ProcessTreeNodeEx* node) {
    // �߽��飺�ڵ�Ϊ��ֱ�ӷ���
    if (node == NULL) {
        fprintf(stderr, "    [-] Invalid ProcessTreeNodeEx (NULL) in resume_process_tree_ex\n");
        return FALSE;
    }

    BOOL is_operation_executed = TRUE; // ����Ƿ�ִ���˻ָ�����
    //printf("\n    [*] Starting to resume process tree node: PID = %d\n", node->pid);

    // �ָ���ǰ���̵������߳�
    if (node->thread_count > 0) {
        // ����߳���Ϣ�Ƿ���Ч
        if (node->thread_ids == NULL || node->original_suspend_counts == NULL) {
            fprintf(stderr, "    [-] Thread info (IDs/counts) is NULL for PID %d, cannot resume threads\n",
                node->pid);
            is_operation_executed = FALSE;
        }
        else {
            //printf("    [*] Starting to resume %lu threads of PID %d...\n",
            //    node->thread_count, node->pid);

            DWORD success_count = 0; // ͳ�Ƴɹ��ָ����߳���
            for (DWORD i = 0; i < node->thread_count; i++) {
                DWORD tid = node->thread_ids[i];
                DWORD original_count = node->original_suspend_counts[i];

                // ���ù��ߺ����ָ������̵߳�ԭ�������
                if (resume_single_thread(tid, original_count)) {
                    success_count++;
                }
                else {
                    fprintf(stderr, "    [-] Resuming thread (TID: %lu) of PID %d failed (index: %lu)\n",
                        tid, node->pid, i);
                }
            }

            // �����ǰ���̵Ļָ����ͳ��
            if (success_count == node->thread_count) {
                //printf("    [+] Successfully resumed ALL %lu threads of PID %d\n",
                //    node->thread_count, node->pid);
            }
            else if (success_count > 0) {
                printf("    [!] Partially resumed threads of PID %d: %lu success, %lu failed\n",
                    node->pid, success_count, node->thread_count - success_count);
                is_operation_executed = FALSE;
            }
            else {
                fprintf(stderr, "    [-] FAILED to resume ANY threads of PID %d\n", node->pid);
                is_operation_executed = FALSE;
            }
        }
    }
    //else {
    //    printf("    [*] No threads to resume for PID %d\n", node->pid);
    //}

    // �ݹ�ָ������ӽ���
    if (node->child_count > 0) {
        //printf("    [*] Found %zu child processes for PID %d, resuming children...\n",
        //    node->child_count, node->pid);

        for (size_t i = 0; i < node->child_count; i++) {
            ProcessTreeNodeEx* child_node = node->children[i];
            if (child_node == NULL) {
                fprintf(stderr, "    [-] Skip NULL child node of PID %d (index: %zu)\n",
                    node->pid, i);
                continue;
            }

            // �ݹ���ã��ָ��ӽ��̵��߳���
            //printf("    [*] Entering child process: PID = %d (parent PID: %d)\n",
            //    child_node->pid, node->pid);
            if (!resume_process_tree_ex(child_node)) {
                fprintf(stderr, "    [-] Failed to execute resume for child PID %d (parent PID: %d)\n",
                    child_node->pid, node->pid);
                is_operation_executed = FALSE;
            }
            //else {
            //    printf("    [+] Completed resuming child process: PID = %d (parent PID: %d)\n",
            //        child_node->pid, node->pid);
            //}
        }
    }
    //else {
    //    printf("    [*] No child processes to resume for PID %d\n", node->pid);
    //}

    return is_operation_executed;
}
