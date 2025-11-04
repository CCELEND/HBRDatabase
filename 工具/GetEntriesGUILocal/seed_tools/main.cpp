
#include "ProcessTreeNode_.h"
#include "SuspendThread_.h"
#include "get_seed_index.h"
#include "get_index_by_seed.h"
#include "tools.h"
#include <iostream>
#include <limits>
using namespace std;

static bool judge_str(string data) {
    //return regex_match(data, regex("^((0|[1-9][0-9]?)|100)$"));
    return regex_match(data, regex("^(0|1)$"));
}
static void input_str(string* data) {
    while (true) {
        getline(cin, *data);
        if (judge_str(*data)) {
            return;
        }
        else {
            cout << "Error data! please input again!" << endl;
            cin.clear(); *data = "";
        }
    }

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


// 获取控制台窗口的宽度
static int get_console_width() {
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    // 获取控制台缓冲区信息
    if (!GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &csbi)) {
        return 80;
    }
    // csbi.srWindow.Right - csbi.srWindow.Left + 1 即为窗口宽度
    return csbi.srWindow.Right - csbi.srWindow.Left + 1;
}

// 居中输出宽字符字符串
static void wprintf_centered(const wchar_t* wide_str) {
    if (wide_str == NULL) return;

    int console_width = get_console_width();  // 获取当前控制台宽度
    int str_len = wcslen(wide_str);           // 计算宽字符字符串长度

    // 若字符串长度 ≥ 控制台宽度，直接左对齐输出
    if (str_len >= console_width) {
        wprintf(L"%ls\n", wide_str);
        return;
    }

    // 计算居中偏移的空格数：(控制台宽度 - 字符串长度) / 2
    int space_count = (console_width - str_len) / 2;
    // 打印偏移空格（宽字符空格用L' '）
    for (int i = 0; i < space_count; i++) {
        wprintf(L" ");
    }
    // 打印居中的字符内容
    wprintf(L"%ls\n", wide_str);
}

int main() {
    setlocale(LC_ALL, "en_US.UTF-8");
    //setlocale(LC_ALL, "zh_CN.UTF-8");
    //SetConsoleOutputCP(CP_UTF8);
    const wchar_t* art[] = {
        L"╔══════════════════════════════════════════════════════════════════════════════════════════════╗",
        L"║    ███████╗ ███████╗ ███████╗ ██████╗     ████████╗  ██████╗   ██████╗  ██╗      ███████╗    ║",
        L"║    ██╔════╝ ██╔════╝ ██╔════╝ ██╔══██╗    ╚══██╔══╝ ██╔═══██╗ ██╔═══██╗ ██║      ██╔════╝    ║",
        L"║    ███████╗ █████╗   █████╗   ██║  ██║       ██║    ██║   ██║ ██║   ██║ ██║      ███████╗    ║",
        L"║    ╚════██║ ██╔══╝   ██╔══╝   ██║  ██║       ██║    ██║   ██║ ██║   ██║ ██║      ╚════██║    ║",
        L"║    ███████║ ███████╗ ███████╗ ██████╔╝       ██║    ╚██████╔╝ ╚██████╔╝ ███████╗ ███████║    ║",
        L"║    ╚══════╝ ╚══════╝ ╚══════╝ ╚═════╝        ╚═╝     ╚═════╝   ╚═════╝  ╚══════╝ ╚══════╝    ║",
        L"╚══════════════════════════════════════════════════════════════════════════════════════════════╝"
    };

    int line_count = sizeof(art) / sizeof(art[0]);
    for (int i = 0; i < line_count; i++) {
        //wprintf(L"%ls\n", art[i]);
        wprintf_centered(art[i]);
    }
    wprintf(L"\n");

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

    string str1;
    stringstream change;
    input_str(&str1);
    change << str1;
    change >> choice;
    if (choice != 0 && choice != 1) {
        fprintf(stderr, "    [-] The input is incorrect!\n");
        system("pause");
        return 1;
    }
    
    uint64_t known_random_seed = 0;
    uint64_t known_change_seed = 0;

    if (choice == 1) {
        // int c;
        // while ((c = getchar()) != '\n' && c != EOF);
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

    PVOID heapBase = GetMainHeapBase(pid);
    printf("0x%llx\n", (uint64_t)heapBase);

    //// 搜索内存
    //printf("\n[*] Searching process memory...\n");
    //if (choice == 0) {
    //    search_process_memory_fast(pid, known_random_seed, known_change_seed, 0); 
    //}
    //else {
    //    search_process_memory_fast(pid, known_random_seed, known_change_seed, 1);
    //}

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