#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <psapi.h>

constexpr size_t BUFFER_SIZE = 4096;
constexpr size_t MAX_PID_LEN = 16;

// 搜索范围（64-bit 用户模式地址空间-私有提交内存）
const uint64_t SEARCH_START = 0x10000000000;
const uint64_t SEARCH_END = 0x30000000000;

// 进程树节点结构
typedef struct ProcessTreeNode {
    DWORD pid;
    struct ProcessTreeNode** children;
    size_t child_count;
} ProcessTreeNode;

// 创建进程树节点
static ProcessTreeNode* create_process_node(DWORD pid)
{
    ProcessTreeNode* node = (ProcessTreeNode*)malloc(sizeof(ProcessTreeNode));
    if (node) {
        node->pid = pid;
        node->children = NULL;
        node->child_count = 0;
    }
    return node;
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

static void handle_found_seed(HANDLE hProcess, uint64_t seed_addr, const char* ability_name, uint64_t seed_value) {
    uint64_t index_addr = seed_addr + 8;
    uint64_t index_value = 0;

    printf("[+] Found %s_seed at address: 0x%llx\n", ability_name, seed_addr);
    printf("    [+] Seed value: %llu\n", seed_value);

    if (ReadProcessMemory(hProcess, (LPCVOID)index_addr, &index_value, sizeof(uint64_t), NULL)) {
        printf("    [+] %s_index: %llu\n", ability_name, index_value);
    }
    else {
        fprintf(stderr, "    [-] Failed to read %s index (Error: %lu)\n", ability_name, GetLastError());
    }
}


static int search_memory_region_by_seed(HANDLE hProcess, uint64_t start_addr, uint64_t end_addr,
    uint64_t known_random_seed, uint64_t known_change_seed)
{
    if (start_addr >= end_addr || end_addr - start_addr > 0x10000000) {
        return 0;
    }

    printf("[*] Searching for seed values in range: 0x%llx - 0x%llx\n", start_addr, end_addr);

    unsigned char* buffer = (unsigned char*)malloc(BUFFER_SIZE);
    if (!buffer) return 0;

    size_t found_random = 0;
    size_t found_change = 0;
    uint64_t current_addr = start_addr;

    while (current_addr < end_addr && (!found_random || !found_change)) {
        SIZE_T bytes_read;
        SIZE_T read_size = (SIZE_T)min(BUFFER_SIZE, (size_t)(end_addr - current_addr));

        if (!ReadProcessMemory(hProcess, (LPCVOID)current_addr, buffer, read_size, &bytes_read) || bytes_read == 0) {
            current_addr += BUFFER_SIZE;
            continue;
        }

        for (SIZE_T i = 0; i <= bytes_read - sizeof(uint64_t); i++) {
            uint64_t current_seed = 0;
            memcpy(&current_seed, buffer + i, sizeof(uint64_t));

            if (!found_random && current_seed == known_random_seed) {
                handle_found_seed(hProcess, current_addr + i, "RandomMainAbility", known_random_seed);
                found_random = 1;
            }

            if (!found_change && current_seed == known_change_seed) {
                handle_found_seed(hProcess, current_addr + i, "ChangeAbility", known_change_seed);
                found_change = 1;
            }

            if (found_random && found_change) break;
        }

        current_addr += bytes_read;
    }

    free(buffer);
    return found_random || found_change;
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
static void search_process_memory_fast(DWORD pid, uint64_t known_random_seed, uint64_t known_change_seed) {
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

        // 直接搜索这个区域
        if (search_memory_region_by_seed(hProcess, search_start, search_end, 
            known_random_seed, known_change_seed)) {
            break;
        }

        addr = region_end;
    }

    CloseHandle(hProcess);
}

int main() {
    const WCHAR* process_name = L"HeavenBurnsRed.exe";

    // 从控制台读取seed值（支持十进制和十六进制）
    uint64_t known_random_seed = 0;
    uint64_t known_change_seed = 0;
    char input[64];

    printf("[*] 请输入 RandomMainAbility_seed 值 (支持10进制或0x开头的16进制): ");
    if (fgets(input, sizeof(input), stdin)) {
        if (input[0] == '0' && (input[1] == 'x' || input[1] == 'X')) {
            known_random_seed = strtoull(input + 2, NULL, 16);
        }
        else {
            known_random_seed = strtoull(input, NULL, 10);
        }
    }

    printf("[*] 请输入 ChangeAbility_seed 值 (支持10进制或0x开头的16进制): ");
    if (fgets(input, sizeof(input), stdin)) {
        if (input[0] == '0' && (input[1] == 'x' || input[1] == 'X')) {
            known_change_seed = strtoull(input + 2, NULL, 16);
        }
        else {
            known_change_seed = strtoull(input, NULL, 10);
        }
    }

    printf("[*] Looking for process: %ls\n", process_name);
    DWORD pid = find_process_id(process_name);
    if (!pid) {
        fprintf(stderr, "    [-] Process %ls not found!\n", process_name);
        system("pause");
        return 1;
    }

    printf("[+] Found %ls with PID: %d\n", process_name, pid);

    // 构建进程树
    ProcessTreeNode* process_tree = build_process_tree(pid);
    if (!process_tree) {
        fprintf(stderr, "    [-] Failed to build process tree\n");
        system("pause");
        return 1;
    }

    // 暂停进程树
    printf("[*] Suspending process tree...\n");
    if (!suspend_process_tree(process_tree)) {
        fprintf(stderr, "    [-] Failed to suspend process tree\n");
        free_process_tree(process_tree);
        system("pause");
        return 1;
    }

    // 搜索内存
    printf("[*] Searching process memory...\n");
    search_process_memory_fast(pid, known_random_seed, known_change_seed);

    // 恢复进程树
    printf("[*] Resuming process tree...\n");
    if (!resume_process_tree(process_tree)) {
        fprintf(stderr, "    [-] Failed to resume process tree\n");
    }

    // 清理资源
    free_process_tree(process_tree);

    printf("[*] Operation completed. Press any key to exit...\n");
    system("pause");

    return 0;
}