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

 

// 检查是否以管理员权限运行
static BOOL IsRunAsAdmin() {
    BOOL isAdmin = FALSE;
    HANDLE hToken = NULL;

    // 打开当前进程的访问令牌
    if (OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        // 获取提升类型信息
        TOKEN_ELEVATION elevation{};
        DWORD dwSize = sizeof(TOKEN_ELEVATION);

        if (GetTokenInformation(hToken, TokenElevation, &elevation, sizeof(elevation), &dwSize)) {
            isAdmin = elevation.TokenIsElevated;
        }
        CloseHandle(hToken);
    }

    return isAdmin;
}

// 请求管理员权限重新启动程序
static void RequestAdminRights() {
    WCHAR szPath[MAX_PATH];
    if (GetModuleFileName(NULL, szPath, ARRAYSIZE(szPath))) {
        SHELLEXECUTEINFO sei = { sizeof(sei) };
        sei.lpVerb = L"runas";  // 请求管理员权限
        sei.lpFile = szPath;
        sei.hwnd = NULL;
        sei.nShow = SW_NORMAL;

        if (ShellExecuteEx(&sei)) {
            exit(0);  // 成功启动管理员模式进程，退出当前进程
        }
    }
}

// 释放进程树
static void free_process_tree(ProcessTreeNode* node)
{
    if (!node) return;

    for (size_t i = 0; i < node->child_count; i++) {
        free_process_tree(node->children[i]);
    }
    free(node->children);
    free(node);

}


// 构建进程树
static ProcessTreeNode* build_process_tree(DWORD pid)
{
    ProcessTreeNode* root = create_process_node(pid);
    if (!root) return NULL;

    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) {
        free(root);
        return NULL;
    }

    // 第一次遍历：收集所有进程信息
    DWORD processes[1024]{};
    DWORD parent_pids[1024]{};
    size_t process_count = 0;

    PROCESSENTRY32 pe{};
    pe.dwSize = sizeof(PROCESSENTRY32);

    // 收集进程信息
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

    // 构建进程树，只处理直接子进程
    for (size_t i = 0; i < process_count; i++) {
        if (parent_pids[i] != pid) continue;

        // 重新分配子节点数组
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

// 暂停进程树
static BOOL suspend_process_tree(ProcessTreeNode* node)
{
    if (!node) return FALSE;

    BOOL success = TRUE;

    // 先暂停子进程
    for (size_t i = 0; i < node->child_count; i++)
    {
        if (!suspend_process_tree(node->children[i])) {
            success = FALSE;
        }
    }

    // 暂停当前进程
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

// 恢复进程树
static BOOL resume_process_tree(ProcessTreeNode* node) {
    if (!node) return FALSE;

    BOOL success = TRUE;

    // 恢复当前进程
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

    // 恢复子进程
    for (size_t i = 0; i < node->child_count; i++) {
        if (!resume_process_tree(node->children[i])) {
            success = FALSE;
        }
    }

    return success;
}


// 查找进程ID
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


// 搜索进程内存-快速定位私有提交内存区域
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

        // 检查内存属性是否满足条件
        if (mbi.State != MEM_COMMIT ||
            mbi.Type != MEM_PRIVATE ||
            !(mbi.Protect & PAGE_READWRITE)) {
            addr = (uint64_t)mbi.BaseAddress + mbi.RegionSize;
            continue;
        }

        uint64_t region_start = (uint64_t)mbi.BaseAddress;
        uint64_t region_end = region_start + mbi.RegionSize;
        uint64_t region_size = mbi.RegionSize;

        // 检查是否在搜索范围内
        if (region_end <= SEARCH_START || region_start >= SEARCH_END) {
            addr = region_end;
            continue;
        }

        // 检查区域大小是否合理
        if (region_size <= 0x10000 || region_size >= 0x10000000) {
            addr = region_end;
            continue;
        }

        // 计算实际搜索范围（处理部分重叠的情况）
        uint64_t search_start = max(region_start, SEARCH_START);
        uint64_t search_end = min(region_end, SEARCH_END);

        // printf("[+] Searching private committed region: 0x%llx - 0x%llx (size: 0x%llx)\n",
        //        search_start, search_end, search_end - search_start);

        // 直接搜索这个区域获取seed和index
        if (flag == 0 && search_memory_region(hProcess, search_start, search_end)) {
            break;
        }
        // 直接搜索这个区域根据seed获取index
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
        L"|    ███████╗ ███████╗ ███████╗ ██████╗     ████████╗  ██████╗   ██████╗  ██╗      ███████╗    |",
        L"|    ██╔════╝ ██╔════╝ ██╔════╝ ██╔══██╗    ╚══██╔══╝ ██╔═══██╗ ██╔═══██╗ ██║      ██╔════╝    |",
        L"|    ███████╗ █████╗   █████╗   ██║  ██║       ██║    ██║   ██║ ██║   ██║ ██║      ███████╗    |",
        L"|    ╚════██║ ██╔══╝   ██╔══╝   ██║  ██║       ██║    ██║   ██║ ██║   ██║ ██║      ╚════██║    |",
        L"|    ███████║ ███████╗ ███████╗ ██████╔╝       ██║    ╚██████╔╝ ╚██████╔╝ ███████╗ ███████║    |",
        L"|    ╚══════╝ ╚══════╝ ╚══════╝ ╚═════╝        ╚═╝     ╚═════╝   ╚═════╝  ╚══════╝ ╚══════╝    |",
        L"+==============================================================================================+"
    };

    int line_count = sizeof(art) / sizeof(art[0]);
    for (int i = 0; i < line_count; i++) {
        wprintf(L"%ls\n", art[i]);
    }
    printf("\n");

    // 检查管理员权限
    if (!IsRunAsAdmin()) {
        printf("[-] The program needs to be run with administrator privileges!\n");
        printf("[*] Requesting administrator permission...\n");

        RequestAdminRights();

        // 如果请求失败，手动以管理员身份运行
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
        // 从控制台读取seed值（支持十进制和十六进制）
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

    // 构建进程树
    ProcessTreeNodeEx* process_tree = build_process_tree_ex(pid);
    if (!process_tree) {
        fprintf(stderr, "    [-] Failed to build process tree!\n");
        system("pause");
        return 1;
    }

    // 暂停进程树
    printf("\n[*] Suspending process tree...\n");
    if (!suspend_process_tree_ex(process_tree)) {
        fprintf(stderr, "    [-] Failed to suspend process tree!\n");
        free_process_tree_ex(process_tree);
        system("pause");
        return 1;
    }

    // 搜索内存
    printf("\n[*] Searching process memory...\n");
    if (choice == 0) {
        search_process_memory_fast(pid, known_random_seed, known_change_seed, 0); 
    }
    else {
        search_process_memory_fast(pid, known_random_seed, known_change_seed, 1);
    }

    // 恢复进程树
    printf("\n[*] Resuming process tree...\n");
    if (!resume_process_tree_ex(process_tree)) {
        fprintf(stderr, "    [-] Failed to resume process tree!\n");
    }

    // 清理资源
    free_process_tree_ex(process_tree);

    printf("[*] Operation completed. Press any key to exit...\n");
    system("pause");

    return 0;
}