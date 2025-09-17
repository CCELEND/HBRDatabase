# include "SuspendThread_.h"

/**
 * @brief 遍历指定PID的所有线程，获取线程ID列表
 * @param pid 目标进程ID
 * @param threads 输出参数：存储线程ID的数组
 * @param max_threads 数组最大容量（避免越界）
 * @return 实际获取的线程数量，0表示失败
 */
static DWORD enum_process_threads(DWORD pid, DWORD* threads, DWORD max_threads) {
    // 入参校验，不满足则直接返回
    if (pid == 0 || threads == NULL || max_threads == 0) {
        fprintf(stderr, "    [-] Invalid parameter for enum_process_threads\n");
        return 0;
    }

    // 创建线程快照，失败则直接返回
    HANDLE hThreadSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (hThreadSnapshot == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "    [-] CreateToolhelp32Snapshot (thread) failed (PID: %d, Error: %lu)\n",
            pid, GetLastError());
        return 0;
    }

    THREADENTRY32 thread_entry = { 0 };
    thread_entry.dwSize = sizeof(THREADENTRY32); // 初始化结构体大小
    DWORD thread_count = 0;

    // 尝试获取第一个线程信息，失败则释放资源并返回
    if (!Thread32First(hThreadSnapshot, &thread_entry)) {
        fprintf(stderr, "    [-] Thread32First failed (PID: %d, Error: %lu)\n",
            pid, GetLastError());
        CloseHandle(hThreadSnapshot);
        return 0;
    }

    // 遍历所有线程
    do {
        // 筛选目标进程的线程
        if (thread_entry.th32OwnerProcessID != pid) continue;


        // 检查是否超出最大线程数限制
        if (thread_count >= max_threads) {
            fprintf(stderr, "    [-] Too many threads (PID: %d, max: %lu), skip remaining\n",
                pid, max_threads);
            break;
        }

        // 记录线程ID
        threads[thread_count++] = thread_entry.th32ThreadID;

    } while (Thread32Next(hThreadSnapshot, &thread_entry));

    // 释放资源并返回结果
    CloseHandle(hThreadSnapshot);
    return thread_count;
}


/**
 * @brief 暂停单个线程，并记录原挂起计数
 * @param tid 目标线程ID
 * @param original_suspend_count 输出参数：存储线程暂停前的挂起计数
 * @return TRUE：暂停成功，FALSE：失败
 */
static BOOL suspend_single_thread(DWORD tid, DWORD* original_suspend_count) {
    if (tid == 0 || original_suspend_count == NULL) {
        fprintf(stderr, "    [-] Invalid parameter for suspend_single_thread\n");
        return FALSE;
    }

    // 打开线程：需 THREAD_SUSPEND_RESUME（暂停/恢复权限）和 THREAD_QUERY_INFORMATION（获取挂起计数权限）
    HANDLE hThread = OpenThread(
        THREAD_SUSPEND_RESUME | THREAD_QUERY_INFORMATION,
        FALSE, // 不继承句柄
        tid
    );
    if (hThread == NULL) {
        fprintf(stderr, "    [-] OpenThread failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        return FALSE;
    }

    // 暂停线程：SuspendThread 返回操作前的挂起计数（0表示未挂起，n表示已被挂起n次）
    DWORD suspend_count = SuspendThread(hThread);
    if (suspend_count == (DWORD)-1) { // 失败返回 -1（即0xFFFFFFFF）
        fprintf(stderr, "    [-] SuspendThread failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        CloseHandle(hThread);
        return FALSE;
    }

    // 记录原挂起计数（后续恢复时需还原到该值）
    *original_suspend_count = suspend_count;
    //printf("        [+] Suspended thread (TID: %lu) | Original suspend count: %lu\n",
    //    tid, suspend_count);

    CloseHandle(hThread); // 释放线程句柄
    return TRUE;
}


/**
 * @brief 恢复单个线程到暂停前的挂起计数状态
 * @param tid 目标线程ID
 * @param original_suspend_count 线程暂停前的挂起计数（由 suspend_single_thread 记录）
 * @return TRUE：恢复成功，FALSE：失败
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

    // 步骤1：获取当前线程的挂起计数（需先暂停一次获取，再撤销该次暂停）
    DWORD current_suspend_count = SuspendThread(hThread); // 暂停一次，返回操作前的计数
    if (current_suspend_count == (DWORD)-1) {
        fprintf(stderr, "    [-] Get suspend count failed (TID: %lu, Error: %lu)\n",
            tid, GetLastError());
        CloseHandle(hThread);
        return FALSE;
    }
    ResumeThread(hThread); // 撤销刚才的暂停，恢复到操作前的计数

    // 计算需要恢复的次数（当前挂起计数 - 原挂起计数）
    DWORD need_resume_count = current_suspend_count - original_suspend_count;
    if (need_resume_count > 0) {
        for (DWORD i = 0; i < need_resume_count; i++) {
            ResumeThread(hThread); // 每次调用减少1个挂起计数
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
 * @brief 创建扩展进程树节点（含线程信息存储）
 * @param pid 目标进程ID
 * @return 节点指针：成功返回非NULL，失败返回NULL
 */
static ProcessTreeNodeEx* create_process_node_ex(DWORD pid) {
    ProcessTreeNodeEx* node = (ProcessTreeNodeEx*)malloc(sizeof(ProcessTreeNodeEx));
    if (node == NULL) {
        fprintf(stderr, "    [-] Malloc ProcessTreeNodeEx failed (PID: %d)\n", pid);
        return NULL;
    }

    // 初始化节点成员
    node->pid = pid;
    node->children = NULL;
    node->child_count = 0;
    node->thread_ids = NULL;
    node->original_suspend_counts = NULL;
    node->thread_count = 0;

    return node;
}

/**
 * @brief 递归释放扩展进程树（含线程信息）
 * @param node 进程树根节点
 */
void free_process_tree_ex(ProcessTreeNodeEx* node) {
    if (node == NULL) return;

    // 递归释放所有子节点
    for (size_t i = 0; i < node->child_count; i++) {
        free_process_tree_ex(node->children[i]);
    }
    free(node->children); // 释放子节点数组

    // 释放线程信息数组
    free(node->thread_ids);
    free(node->original_suspend_counts);

    free(node); // 释放当前节点
}


/**
 * @brief 递归构建进程树（含每个进程的线程信息）
 * @param root_pid 进程树根节点PID（目标主进程PID）
 * @return 进程树根节点指针：成功返回非NULL，失败返回NULL
 */
ProcessTreeNodeEx* build_process_tree_ex(DWORD root_pid) {
    // 创建当前进程节点（提前返回无效节点）
    ProcessTreeNodeEx* root_node = create_process_node_ex(root_pid);
    if (root_node == NULL) {
        fprintf(stderr, "    [-] Create root node failed (PID: %d)\n", root_pid);
        return NULL;
    }

    // 为当前节点获取并初始化线程信息
    DWORD threads[MAX_THREADS_PER_PROCESS] = { 0 };
    DWORD thread_count = enum_process_threads(root_pid, threads, MAX_THREADS_PER_PROCESS);

    // 仅当线程数 > 0 时，才分配内存存储线程信息
    if (thread_count > 0) {
        // 分配线程ID和挂起计数数组（两个数组需同时成功，否则释放已分配资源）
        root_node->thread_ids = (DWORD*)malloc(thread_count * sizeof(DWORD));
        root_node->original_suspend_counts = (DWORD*)malloc(thread_count * sizeof(DWORD));

        // 内存分配失败：释放所有已分配资源，返回NULL
        if (root_node->thread_ids == NULL || root_node->original_suspend_counts == NULL) {
            fprintf(stderr, "    [-] Malloc thread info failed (PID: %d)\n", root_pid);
            free(root_node->thread_ids);    // 即使为NULL，free也安全
            free(root_node->original_suspend_counts);
            free_process_tree_ex(root_node); // 释放整个根节点
            return NULL;
        }

        // 复制线程ID到节点，初始化线程数
        memcpy(root_node->thread_ids, threads, thread_count * sizeof(DWORD));
        root_node->thread_count = thread_count;
        //printf("    [+] Process (PID: %d) has %lu threads\n", root_pid, thread_count);
    }
    //else {
    //    // 线程数为0（枚举失败或无线程），无需分配内存
    //    printf("    [+] Process (PID: %d) has no threads (or enum failed)\n", root_pid);
    //}

    // 创建进程快照（失败则清理根节点并返回）
    HANDLE hProcessSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hProcessSnapshot == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "    [-] Create process snapshot failed (PID: %d, Error: %lu)\n",
            root_pid, GetLastError());
        free_process_tree_ex(root_node); // 清理已创建的根节点
        return NULL;
    }

    // 遍历系统进程，递归构建子进程树
    PROCESSENTRY32 process_entry = { 0 };
    process_entry.dwSize = sizeof(PROCESSENTRY32); // 初始化结构体大小

    // 尝试获取第一个进程信息：失败则清理快照和根节点
    if (!Process32First(hProcessSnapshot, &process_entry)) {
        fprintf(stderr, "    [-] Process32First failed (PID: %d, Error: %lu)\n",
            root_pid, GetLastError());
        CloseHandle(hProcessSnapshot);   // 释放快照句柄
        free_process_tree_ex(root_node); // 清理根节点
        return NULL;
    }

    // 遍历所有进程
    do {
        // 跳过：当前进程不是根节点的子进程（父PID不匹配）
        if (process_entry.th32ParentProcessID != root_pid) continue;

        // 递归创建子进程节点（含子进程的线程信息）
        ProcessTreeNodeEx* child_node = build_process_tree_ex(process_entry.th32ProcessID);
        // 跳过：子节点创建失败（无需处理，继续遍历下一个进程）
        if (child_node == NULL) {
            fprintf(stderr, "    [-] Create child node failed (Child PID: %d, Parent PID: %d)\n",
                process_entry.th32ProcessID, root_pid);
            continue;
        }

        // 扩展子进程数组（realloc 重新分配内存）
        ProcessTreeNodeEx** new_children = (ProcessTreeNodeEx**)realloc(
            root_node->children,
            (root_node->child_count + 1) * sizeof(ProcessTreeNodeEx*)
        );
        // 内存分配失败：释放当前子节点，继续遍历（不影响其他子进程）
        if (new_children == NULL) {
            fprintf(stderr, "    [-] Realloc child array failed (Child PID: %d, Parent PID: %d)\n",
                process_entry.th32ProcessID, root_pid);
            free_process_tree_ex(child_node);
            continue;
        }

        // 成功添加子节点到根节点
        root_node->children = new_children;
        root_node->children[root_node->child_count++] = child_node;
        //printf("    [+] Added child process (PID: %d) to parent (PID: %d)\n",
        //    process_entry.th32ProcessID, root_pid);

    } while (Process32Next(hProcessSnapshot, &process_entry));

    // 清理资源并返回根节点
    CloseHandle(hProcessSnapshot); // 释放进程快照句柄
    return root_node;
}



/**
 * @brief 递归暂停进程树中所有进程的所有线程
 * @param node 进程树节点（当前要处理的进程）
 * @return BOOL：TRUE表示当前节点及子节点的暂停操作已执行（即使部分线程失败），FALSE表示节点无效
 * @note 暂停顺序：先递归暂停所有子进程 → 再暂停当前进程的线程（避免子进程被父进程唤醒）
 */
BOOL suspend_process_tree_ex(ProcessTreeNodeEx* node) {
    // 边界检查：节点为空直接返回
    if (node == NULL) {
        fprintf(stderr, "    [-] Invalid ProcessTreeNodeEx (NULL) in suspend_process_tree_ex\n");
        return FALSE;
    }

    BOOL is_operation_executed = TRUE; // 标记是否执行了暂停操作（即使部分线程失败）
    //printf("\n    [*] Starting to suspend process tree node: PID = %d\n", node->pid);

    // 递归暂停所有子进程
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

            // 递归调用，暂停子进程的线程树
            //printf("    [*] Entering child process: PID = %d (parent PID: %d)\n",
            //    child_node->pid, node->pid);
            if (!suspend_process_tree_ex(child_node)) {
                fprintf(stderr, "    [-] Failed to execute suspend for child PID %d (parent PID: %d)\n",
                    child_node->pid, node->pid);
                is_operation_executed = FALSE; // 子进程暂停操作执行失败，标记整体状态
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

    // 暂停当前进程的所有线程
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

    DWORD success_count = 0; // 统计成功暂停的线程数
    for (DWORD i = 0; i < node->thread_count; i++) {
        DWORD tid = node->thread_ids[i];
        // 调用工具函数暂停单个线程，并记录原挂起计数到节点的 original_suspend_counts 数组
        if (suspend_single_thread(tid, &(node->original_suspend_counts[i]))) {
            success_count++;
        }
        else {
            fprintf(stderr, "    [-] Suspending thread (TID: %lu) of PID %d failed (index: %lu)\n",
                tid, node->pid, i);
        }
    }

    // 输出当前进程的暂停结果统计
    if (success_count == node->thread_count) {
        //printf("    [+] Successfully suspended ALL %lu threads of PID %d\n",
        //    node->thread_count, node->pid);
    }
    else if (success_count > 0) {
        printf("    [!] Partially suspended threads of PID %d: %lu success, %lu failed\n",
            node->pid, success_count, node->thread_count - success_count);
        is_operation_executed = FALSE; // 部分失败，标记整体状态
    }
    else {
        fprintf(stderr, "    [-] FAILED to suspend ANY threads of PID %d\n", node->pid);
        is_operation_executed = FALSE;
    }

    return is_operation_executed;
}

/**
 * @brief 递归恢复进程树中所有进程的所有线程
 * @param node 进程树节点（当前要处理的进程）
 * @return BOOL：TRUE表示恢复操作已执行（即使部分线程失败），FALSE表示节点无效
 * @note 恢复顺序：先恢复当前进程的线程 → 再递归恢复所有子进程（与暂停顺序相反）
 */
BOOL resume_process_tree_ex(ProcessTreeNodeEx* node) {
    // 边界检查：节点为空直接返回
    if (node == NULL) {
        fprintf(stderr, "    [-] Invalid ProcessTreeNodeEx (NULL) in resume_process_tree_ex\n");
        return FALSE;
    }

    BOOL is_operation_executed = TRUE; // 标记是否执行了恢复操作
    //printf("\n    [*] Starting to resume process tree node: PID = %d\n", node->pid);

    // 恢复当前进程的所有线程
    if (node->thread_count > 0) {
        // 检查线程信息是否有效
        if (node->thread_ids == NULL || node->original_suspend_counts == NULL) {
            fprintf(stderr, "    [-] Thread info (IDs/counts) is NULL for PID %d, cannot resume threads\n",
                node->pid);
            is_operation_executed = FALSE;
        }
        else {
            //printf("    [*] Starting to resume %lu threads of PID %d...\n",
            //    node->thread_count, node->pid);

            DWORD success_count = 0; // 统计成功恢复的线程数
            for (DWORD i = 0; i < node->thread_count; i++) {
                DWORD tid = node->thread_ids[i];
                DWORD original_count = node->original_suspend_counts[i];

                // 调用工具函数恢复单个线程到原挂起计数
                if (resume_single_thread(tid, original_count)) {
                    success_count++;
                }
                else {
                    fprintf(stderr, "    [-] Resuming thread (TID: %lu) of PID %d failed (index: %lu)\n",
                        tid, node->pid, i);
                }
            }

            // 输出当前进程的恢复结果统计
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

    // 递归恢复所有子进程
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

            // 递归调用，恢复子进程的线程树
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
