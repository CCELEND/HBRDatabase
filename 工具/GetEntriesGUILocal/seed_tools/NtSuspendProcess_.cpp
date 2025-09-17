
# include "ProcessTreeNode_.h"

// ���� NtSuspendProcess
// ���� NtSuspendProcess �� NtResumeProcess �ĺ���ָ������
typedef NTSTATUS(NTAPI* PFN_NtSuspendProcess)(HANDLE ProcessHandle);
typedef NTSTATUS(NTAPI* PFN_NtResumeProcess)(HANDLE ProcessHandle);

// ȫ�ֺ���ָ�룬�洢��̬���ص�API��ַ
static PFN_NtSuspendProcess g_pNtSuspendProcess = NULL;
static PFN_NtResumeProcess g_pNtResumeProcess = NULL;

// ��ʼ�� NtSuspendProcess �� NtResumeProcess
static BOOL InitUndocumentedAPIs() {
    // ���� ntdll.dll
    HMODULE hNtdll = LoadLibraryW(L"ntdll.dll");
    if (hNtdll == NULL) {
        fprintf(stderr, "[-] LoadLibrary ntdll.dll failed (Error: %lu)\n", GetLastError());
        return FALSE;
    }

    // ��ȡ NtSuspendProcess ��ַ
    g_pNtSuspendProcess = (PFN_NtSuspendProcess)GetProcAddress(hNtdll, "NtSuspendProcess");
    // ��ȡ NtResumeProcess ��ַ
    g_pNtResumeProcess = (PFN_NtResumeProcess)GetProcAddress(hNtdll, "NtResumeProcess");

    if (g_pNtSuspendProcess == NULL || g_pNtResumeProcess == NULL) {
        fprintf(stderr, "[-] GetProcAddress failed for NtSuspendProcess/NtResumeProcess (Error: %lu)\n", GetLastError());
        FreeLibrary(hNtdll);
        return FALSE;
    }

    return TRUE;
}
// ��ͣ������
static BOOL suspend_process_tree_nt(ProcessTreeNode* node) {
    if (!node) return FALSE;
    if (g_pNtSuspendProcess == NULL) return FALSE; // ȷ��API�ѳ�ʼ��

    BOOL success = TRUE;

    // �ݹ���ͣ�����ӽ���
    for (size_t i = 0; i < node->child_count; i++) {
        if (!suspend_process_tree_nt(node->children[i])) {
            success = FALSE;
        }
    }

    // �򿪽��̣����� PROCESS_SUSPEND_RESUME Ȩ�ޣ��� PROCESS_ALL_ACCESS ����ȫ��
    HANDLE hProcess = OpenProcess(PROCESS_SUSPEND_RESUME, FALSE, node->pid);
    if (hProcess) {
        // ���� NtSuspendProcess ��ͣ����
        NTSTATUS status = g_pNtSuspendProcess(hProcess);
        if (status >= 0) { // NTSTATUS >=0 ��ʾ�ɹ�
            printf("    [+] Suspended process (NT) : %d\n", node->pid);
        }
        else {
            fprintf(stderr, "    [-] Failed to suspend process (NT): %d (NTSTATUS: 0x%X)\n", node->pid, status);
            success = FALSE;
        }
        CloseHandle(hProcess); // �ͷž��
    }
    else {
        fprintf(stderr, "    [-] Failed to open process: %d (Error: %lu)\n", node->pid, GetLastError());
        success = FALSE;
    }

    return success;
}
// �ָ�������
static BOOL resume_process_tree_nt(ProcessTreeNode* node) {
    if (!node) return FALSE;
    if (g_pNtResumeProcess == NULL) return FALSE;

    BOOL success = TRUE;

    // �Ȼָ������̣��ٵݹ�ָ��ӽ���
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

    // �ָ��ӽ���
    for (size_t i = 0; i < node->child_count; i++) {
        if (!resume_process_tree_nt(node->children[i])) {
            success = FALSE;
        }
    }

    return success;
}