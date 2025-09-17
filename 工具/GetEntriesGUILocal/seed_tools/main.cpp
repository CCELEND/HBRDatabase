#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <psapi.h>
#include <wchar.h>
#include <locale.h>

#include "ProcessTreeNode_.h"
#include "SuspendThread_.h"
#include "get_seed_index.h"
#include "get_index_by_seed.h"

 

// ����Ƿ��Թ���ԱȨ������
static BOOL IsRunAsAdmin() {
    BOOL isAdmin = FALSE;
    HANDLE hToken = NULL;

    // �򿪵�ǰ���̵ķ�������
    if (OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        // ��ȡ����������Ϣ
        TOKEN_ELEVATION elevation{};
        DWORD dwSize = sizeof(TOKEN_ELEVATION);

        if (GetTokenInformation(hToken, TokenElevation, &elevation, sizeof(elevation), &dwSize)) {
            isAdmin = elevation.TokenIsElevated;
        }
        CloseHandle(hToken);
    }

    return isAdmin;
}

// �������ԱȨ��������������
static void RequestAdminRights() {
    WCHAR szPath[MAX_PATH];
    if (GetModuleFileName(NULL, szPath, ARRAYSIZE(szPath))) {
        SHELLEXECUTEINFO sei = { sizeof(sei) };
        sei.lpVerb = L"runas";  // �������ԱȨ��
        sei.lpFile = szPath;
        sei.hwnd = NULL;
        sei.nShow = SW_NORMAL;

        if (ShellExecuteEx(&sei)) {
            exit(0);  // �ɹ���������Աģʽ���̣��˳���ǰ����
        }
    }
}

// �ͷŽ�����
static void free_process_tree(ProcessTreeNode* node)
{
    if (!node) return;

    for (size_t i = 0; i < node->child_count; i++) {
        free_process_tree(node->children[i]);
    }
    free(node->children);
    free(node);

}


// ����������
static ProcessTreeNode* build_process_tree(DWORD pid)
{
    ProcessTreeNode* root = create_process_node(pid);
    if (!root) return NULL;

    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) {
        free(root);
        return NULL;
    }

    // ��һ�α������ռ����н�����Ϣ
    DWORD processes[1024]{};
    DWORD parent_pids[1024]{};
    size_t process_count = 0;

    PROCESSENTRY32 pe{};
    pe.dwSize = sizeof(PROCESSENTRY32);

    // �ռ�������Ϣ
    if (!Process32First(hSnapshot, &pe)) {
        CloseHandle(hSnapshot);
        free(root);
        return NULL;
    }

    do {
        if (process_count >= 1024) break;
        processes[process_count] = pe.th32ProcessID;
        parent_pids[process_count] = pe.th32ParentProcessID;
        process_count++;
    } while (Process32Next(hSnapshot, &pe));

    // ������������ֻ����ֱ���ӽ���
    for (size_t i = 0; i < process_count; i++) {
        if (parent_pids[i] != pid) continue;

        // ���·����ӽڵ�����
        ProcessTreeNode** new_children = (ProcessTreeNode**)realloc(
            root->children, (root->child_count + 1) * sizeof(ProcessTreeNode*));

        if (!new_children) continue;

        root->children = new_children;
        ProcessTreeNode* child_node = create_process_node(processes[i]);

        if (!child_node) continue;

        root->children[root->child_count] = child_node;
        root->child_count++;
    }

    CloseHandle(hSnapshot);
    return root;
}

// ��ͣ������
static BOOL suspend_process_tree(ProcessTreeNode* node)
{
    if (!node) return FALSE;

    BOOL success = TRUE;

    // ����ͣ�ӽ���
    for (size_t i = 0; i < node->child_count; i++)
    {
        if (!suspend_process_tree(node->children[i])) {
            success = FALSE;
        }
    }

    // ��ͣ��ǰ����
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, node->pid);
    if (hProcess) {
        if (!DebugActiveProcess(node->pid)) {
            fprintf(stderr, "    [-] Failed to suspend process: %d\n", node->pid);
            success = FALSE;
        }
        else {
            printf("    [+] Suspended process: %d\n", node->pid);
        }
        CloseHandle(hProcess);
    }
    else {
        fprintf(stderr, "    [-] Failed to open process: %d (Error: %lu)\n", node->pid, GetLastError());
        success = FALSE;
    }

    return success;
}

// �ָ�������
static BOOL resume_process_tree(ProcessTreeNode* node) {
    if (!node) return FALSE;

    BOOL success = TRUE;

    // �ָ���ǰ����
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, node->pid);
    if (hProcess) {
        if (!DebugActiveProcessStop(node->pid)) {
            fprintf(stderr, "    [-] Failed to resume process: %d\n", node->pid);
            success = FALSE;
        }
        else {
            printf("    [+] Resumed process: %d\n", node->pid);
        }
        CloseHandle(hProcess);
    }
    else {
        fprintf(stderr, "    [-] Failed to open process: %d (Error: %lu)\n", node->pid, GetLastError());
        success = FALSE;
    }

    // �ָ��ӽ���
    for (size_t i = 0; i < node->child_count; i++) {
        if (!resume_process_tree(node->children[i])) {
            success = FALSE;
        }
    }

    return success;
}


// ���ҽ���ID
static DWORD find_process_id(const WCHAR* process_name) {
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) return 0;

    PROCESSENTRY32W pe = { sizeof(PROCESSENTRY32W) };
    DWORD pid = 0;

    for (BOOL success = Process32FirstW(hSnapshot, &pe);
        success && pid == 0;
        success = Process32NextW(hSnapshot, &pe)) {
        if (_wcsicmp(pe.szExeFile, process_name) == 0) {
            pid = pe.th32ProcessID;
        }
    }

    CloseHandle(hSnapshot);
    return pid;
}


// ���������ڴ�-���ٶ�λ˽���ύ�ڴ�����
static void search_process_memory_fast(DWORD pid, 
    uint64_t known_random_seed, uint64_t known_change_seed, 
    size_t flag) {
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!hProcess) {
        fprintf(stderr, "[-] OpenProcess failed for PID %d (Error: %lu)\n", pid, GetLastError());
        return;
    }

    printf("[*] Fast searching private committed memory in range 0x%llx-0x%llx...\n",
        SEARCH_START, SEARCH_END);

    MEMORY_BASIC_INFORMATION mbi;
    uint64_t addr = SEARCH_START;

    while (addr < SEARCH_END) {
        if (!VirtualQueryEx(hProcess, (LPCVOID)addr, &mbi, sizeof(mbi))) {
            break;
        }

        // ����ڴ������Ƿ���������
        if (mbi.State != MEM_COMMIT ||
            mbi.Type != MEM_PRIVATE ||
            !(mbi.Protect & PAGE_READWRITE)) {
            addr = (uint64_t)mbi.BaseAddress + mbi.RegionSize;
            continue;
        }

        uint64_t region_start = (uint64_t)mbi.BaseAddress;
        uint64_t region_end = region_start + mbi.RegionSize;
        uint64_t region_size = mbi.RegionSize;

        // ����Ƿ���������Χ��
        if (region_end <= SEARCH_START || region_start >= SEARCH_END) {
            addr = region_end;
            continue;
        }

        // ��������С�Ƿ����
        if (region_size <= 0x10000 || region_size >= 0x10000000) {
            addr = region_end;
            continue;
        }

        // ����ʵ��������Χ���������ص��������
        uint64_t search_start = max(region_start, SEARCH_START);
        uint64_t search_end = min(region_end, SEARCH_END);

        // printf("[+] Searching private committed region: 0x%llx - 0x%llx (size: 0x%llx)\n",
        //        search_start, search_end, search_end - search_start);

        // ֱ��������������ȡseed��index
        if (flag == 0 && search_memory_region(hProcess, search_start, search_end)) {
            break;
        }
        // ֱ����������������seed��ȡindex
        if (flag == 1 && search_memory_region_by_seed(hProcess, search_start, search_end,
            known_random_seed, known_change_seed)) {
            break;
        }



        addr = region_end;
    }

    CloseHandle(hProcess);
}

int main() {
    setlocale(LC_ALL, "en_US.UTF-8");
    //setlocale(LC_ALL, "zh_CN.UTF-8");
    const wchar_t* art[] = {
        L"+==============================================================================================+",
        L"|    ���������������[ ���������������[ ���������������[ �������������[     �����������������[  �������������[   �������������[  �����[      ���������������[    |",
        L"|    �����X�T�T�T�T�a �����X�T�T�T�T�a �����X�T�T�T�T�a �����X�T�T�����[    �^�T�T�����X�T�T�a �����X�T�T�T�����[ �����X�T�T�T�����[ �����U      �����X�T�T�T�T�a    |",
        L"|    ���������������[ �����������[   �����������[   �����U  �����U       �����U    �����U   �����U �����U   �����U �����U      ���������������[    |",
        L"|    �^�T�T�T�T�����U �����X�T�T�a   �����X�T�T�a   �����U  �����U       �����U    �����U   �����U �����U   �����U �����U      �^�T�T�T�T�����U    |",
        L"|    ���������������U ���������������[ ���������������[ �������������X�a       �����U    �^�������������X�a �^�������������X�a ���������������[ ���������������U    |",
        L"|    �^�T�T�T�T�T�T�a �^�T�T�T�T�T�T�a �^�T�T�T�T�T�T�a �^�T�T�T�T�T�a        �^�T�a     �^�T�T�T�T�T�a   �^�T�T�T�T�T�a  �^�T�T�T�T�T�T�a �^�T�T�T�T�T�T�a    |",
        L"+==============================================================================================+"
    };

    int line_count = sizeof(art) / sizeof(art[0]);
    for (int i = 0; i < line_count; i++) {
        wprintf(L"%ls\n", art[i]);
    }
    printf("\n");

    // ������ԱȨ��
    if (!IsRunAsAdmin()) {
        printf("[-] The program needs to be run with administrator privileges!\n");
        printf("[*] Requesting administrator permission...\n");

        RequestAdminRights();

        // �������ʧ�ܣ��ֶ��Թ���Ա�������
        printf("[-] The request for administrator privileges failed. Please manually run the program as an administrator.\n");
        system("pause");
        return 1;
    }

    printf("[+] The program runs with administrator privileges.\n\n");

    size_t choice = 0;
    printf("0. Get seed and index\n");
    printf("1. Get index by seed\n");
    printf("[*] Please input your choice >> ");
    scanf_s("%lld", &choice);

    if (choice != 0 && choice != 1) {
        fprintf(stderr, "    [-] The input is incorrect!\n");
        system("pause");
        return 1;
    }
    
    uint64_t known_random_seed = 0;
    uint64_t known_change_seed = 0;

    if (choice == 1) {
        int c;
        while ((c = getchar()) != '\n' && c != EOF);
        // �ӿ���̨��ȡseedֵ��֧��ʮ���ƺ�ʮ�����ƣ�
        get_RandomMainAbility_seed_ChangeAbility_seed(known_random_seed, known_change_seed);
    }

    const WCHAR* process_name = L"HeavenBurnsRed.exe";
    printf("\n[*] Looking for process: %ls\n", process_name);
    DWORD pid = find_process_id(process_name);
    if (!pid) {
        fprintf(stderr, "    [-] Process %ls not found!\n", process_name);
        system("pause");
        return 1;
    }

    printf("[+] Found %ls with PID: %d\n", process_name, pid);

    // ����������
    ProcessTreeNodeEx* process_tree = build_process_tree_ex(pid);
    if (!process_tree) {
        fprintf(stderr, "    [-] Failed to build process tree!\n");
        system("pause");
        return 1;
    }

    // ��ͣ������
    printf("\n[*] Suspending process tree...\n");
    if (!suspend_process_tree_ex(process_tree)) {
        fprintf(stderr, "    [-] Failed to suspend process tree!\n");
        free_process_tree_ex(process_tree);
        system("pause");
        return 1;
    }

    // �����ڴ�
    printf("\n[*] Searching process memory...\n");
    if (choice == 0) {
        search_process_memory_fast(pid, known_random_seed, known_change_seed, 0); 
    }
    else {
        search_process_memory_fast(pid, known_random_seed, known_change_seed, 1);
    }

    // �ָ�������
    printf("\n[*] Resuming process tree...\n");
    if (!resume_process_tree_ex(process_tree)) {
        fprintf(stderr, "    [-] Failed to resume process tree!\n");
    }

    // ������Դ
    free_process_tree_ex(process_tree);

    printf("[*] Operation completed. Press any key to exit...\n");
    system("pause");

    return 0;
}