#include "get_seed_index.h"


// �����ֽ�����
const unsigned char pattern[] = {
    0x4C, 0x00, 0x6F, 0x00, 0x74, 0x00, 0x74, 0x00,
    0x65, 0x00, 0x72, 0x00, 0x79, 0x00, 0x46, 0x00,
    0x65, 0x00, 0x61, 0x00, 0x74, 0x00, 0x68, 0x00,
    0x65, 0x00, 0x72, 0x00
};
const size_t pattern_size = sizeof(pattern);

// �ڴ���������ƥ��
static size_t find_pattern_in_buffer(const unsigned char* buffer, size_t buffer_size,
    const unsigned char* pattern, size_t pattern_size) {
    if (buffer_size < pattern_size) return -1;

    for (size_t i = 0; i <= buffer_size - pattern_size; i++) {
        if (memcmp(buffer + i, pattern, pattern_size) == 0) {
            return i;
        }
    }
    return -1;
}
// �����ڴ�����
int search_memory_region(HANDLE hProcess, uint64_t start_addr, uint64_t end_addr)
{
    if (start_addr >= end_addr || end_addr - start_addr > 0x10000000) {
        return 0;
    }

    printf("[*] Searching range: 0x%llx - 0x%llx (size: 0x%llx)\n",
        start_addr, end_addr, end_addr - start_addr);

    unsigned char* buffer = (unsigned char*)malloc(BUFFER_SIZE);
    if (!buffer) {
        fprintf(stderr, "[-] Memory allocation failed\n");
        return 0;
    }

    int found = 0;
    uint64_t current_addr = start_addr;

    while (current_addr < end_addr && !found) {
        SIZE_T bytes_read;
        SIZE_T read_size = (SIZE_T)min(BUFFER_SIZE, (size_t)(end_addr - current_addr));

        // ����ȡ�Ƿ�ɹ�
        if (!ReadProcessMemory(hProcess, (LPCVOID)current_addr, buffer, read_size, &bytes_read)
            || bytes_read == 0) {
            current_addr += BUFFER_SIZE;
            continue;
        }

        SIZE_T offset = find_pattern_in_buffer(buffer, bytes_read, pattern, pattern_size);
        if (offset == -1) {
            current_addr += bytes_read;
            continue;
        }

        // �ҵ��������к���
        uint64_t pattern_addr = current_addr + offset;
        printf("[+] Found pattern at address: 0x%llx\n", pattern_addr);
        printf("    [+] RandomMainAbility_seed addr: 0x%llx\n", pattern_addr - 0x204);
        printf("    [+] ChangeAbility_seed addr: 0x%llx\n", pattern_addr - 0x104);

        uint64_t RandomMainAbility_seed = 0, RandomMainAbility_index = 0;
        uint64_t ChangeAbility_seed = 0, ChangeAbility_index = 0;

        // ��ȡ RandomMainAbility ����
        BOOL readRandomSuccess = ReadProcessMemory(hProcess, (LPCVOID)(pattern_addr - 0x204),
            &RandomMainAbility_seed, sizeof(uint64_t), NULL);
        readRandomSuccess &= ReadProcessMemory(hProcess, (LPCVOID)(pattern_addr - 0x204 + 8),
            &RandomMainAbility_index, sizeof(uint64_t), NULL);

        if (readRandomSuccess) {
            printf("    [+] RandomMainAbility_seed: %llu\n", RandomMainAbility_seed);
            printf("    [+] RandomMainAbility_index: %llu\n", RandomMainAbility_index);
        }
        else {
            fprintf(stderr, "    [-] Failed to read RandomMainAbility data (Error: %lu)\n",
                GetLastError());
        }

        // ��ȡ ChangeAbility ����
        BOOL readChangeSuccess = ReadProcessMemory(hProcess, (LPCVOID)(pattern_addr - 0x104),
            &ChangeAbility_seed, sizeof(uint64_t), NULL);
        readChangeSuccess &= ReadProcessMemory(hProcess, (LPCVOID)(pattern_addr - 0x104 + 8),
            &ChangeAbility_index, sizeof(uint64_t), NULL);

        if (readChangeSuccess) {
            printf("    [+] ChangeAbility_seed: %llu\n", ChangeAbility_seed);
            printf("    [+] ChangeAbility_index: %llu\n", ChangeAbility_index);
        }
        else {
            fprintf(stderr, "    [-] Failed to read ChangeAbility data (Error: %lu)\n",
                GetLastError());
        }

        found = 1;
        current_addr += bytes_read;
    }

    free(buffer);
    return found;
}