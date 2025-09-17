
# include "ProcessTreeNode_.h"

// 基于 NtSuspendProcess
// 定义 NtSuspendProcess 和 NtResumeProcess 的函数指针类型
typedef NTSTATUS(NTAPI* PFN_NtSuspendProcess)(HANDLE ProcessHandle);
typedef NTSTATUS(NTAPI* PFN_NtResumeProcess)(HANDLE ProcessHandle);

// 全局函数指针，存储动态加载的API地址
static PFN_NtSuspendProcess g_pNtSuspendProcess = NULL;
static PFN_NtResumeProcess g_pNtResumeProcess = NULL;

// 初始化 NtSuspendProcess 和 NtResumeProcess
static BOOL InitUndocumentedAPIs() {
    // 加载 ntdll.dll
    HMODULE hNtdll = LoadLibraryW(L"ntdll.dll");
    if (hNtdll == NULL) {
        fprintf(stderr, "[-] LoadLibrary ntdll.dll failed (Error: %lu)\n", GetLastError());
        return FALSE;
    }

    // 获取 NtSuspendProcess 地址
    g_pNtSuspendProcess = (PFN_NtSuspendProcess)GetProcAddress(hNtdll, "NtSuspendProcess");
    // 获取 NtResumeProcess 地址
    g_pNtResumeProcess = (PFN_NtResumeProcess)GetProcAddress(hNtdll, "NtResumeProcess");

    if (g_pNtSuspendProcess == NULL || g_pNtResumeProcess == NULL) {
        fprintf(stderr, "[-] GetProcAddress failed for NtSuspendProcess/NtResumeProcess (Error: %lu)\n", GetLastError());
        FreeLibrary(hNtdll);
        return FALSE;
    }

    return TRUE;
}
// 暂停进程树
static BOOL suspend_process_tree_nt(ProcessTreeNode* node) {
    if (!node) return FALSE;
    if (g_pNtSuspendProcess == NULL) return FALSE; // 确保API已初始化

    BOOL success = TRUE;

    // 递归暂停所有子进程
    for (size_t i = 0; i < node->child_count; i++) {
        if (!suspend_process_tree_nt(node->children[i])) {
            success = FALSE;
        }
    }

    // 打开进程（仅需 PROCESS_SUSPEND_RESUME 权限，比 PROCESS_ALL_ACCESS 更安全）
    HANDLE hProcess = OpenProcess(PROCESS_SUSPEND_RESUME, FALSE, node->pid);
    if (hProcess) {
        // 调用 NtSuspendProcess 暂停进程
        NTSTATUS status = g_pNtSuspendProcess(hProcess);
        if (status >= 0) { // NTSTATUS >=0 表示成功
            printf("    [+] Suspended process (NT) : %d\n", node->pid);
        }
        else {
            fprintf(stderr, "    [-] Failed to suspend process (NT): %d (NTSTATUS: 0x%X)\n", node->pid, status);
            success = FALSE;
        }
        CloseHandle(hProcess); // 释放句柄
    }
    else {
        fprintf(stderr, "    [-] Failed to open process: %d (Error: %lu)\n", node->pid, GetLastError());
        success = FALSE;
    }

    return success;
}
// 恢复进程树
static BOOL resume_process_tree_nt(ProcessTreeNode* node) {
    if (!node) return FALSE;
    if (g_pNtResumeProcess == NULL) return FALSE;

    BOOL success = TRUE;

    // 先恢复父进程，再递归恢复子进程
    HANDLE hProcess = OpenProcess(PROCESS_SUSPEND_RESUME, FALSE, node->pid);
    if (hProcess) {
        NTSTATUS status = g_pNtResumeProcess(hProcess);
        if (status >= 0) {
            printf("    [+] Resumed process (NT)   : %d\n", node->pid);
        }
        else {
            fprintf(stderr, "    [-] Failed to resume process (NT): %d (NTSTATUS: 0x%X)\n", node->pid, status);
            success = FALSE;
        }
        CloseHandle(hProcess);
    }
    else {
        fprintf(stderr, "    [-] Failed to open process: %d (Error: %lu)\n", node->pid, GetLastError());
        success = FALSE;
    }

    // 恢复子进程
    for (size_t i = 0; i < node->child_count; i++) {
        if (!resume_process_tree_nt(node->children[i])) {
            success = FALSE;
        }
    }

    return success;
}