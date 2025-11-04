

#include "tools.h"

// 获取堆基址
PVOID GetMainHeapBase(DWORD pid) 
{
    HANDLE hHeapSnap = CreateToolhelp32Snapshot(TH32CS_SNAPHEAPLIST, pid);
    if (hHeapSnap == INVALID_HANDLE_VALUE) {
        return NULL;
    }

    HEAPLIST32 hl32{};
    hl32.dwSize = sizeof(HEAPLIST32);
    PVOID heapBase = NULL;

    if (Heap32ListFirst(hHeapSnap, &hl32)) {
        // 获取第一个堆，通常是默认堆
        HEAPENTRY32 he32{};
        he32.dwSize = sizeof(HEAPENTRY32);

        if (Heap32First(&he32, pid, hl32.th32HeapID)) {
            heapBase = (PVOID)he32.dwAddress;
        }
    }

    CloseHandle(hHeapSnap);
    return heapBase;
}


// 检查是否以管理员权限运行
BOOL IsRunAsAdmin() {
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
void RequestAdminRights() {
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