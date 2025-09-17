
#include "get_index_by_seed.h"

void get_RandomMainAbility_seed_ChangeAbility_seed(uint64_t& known_random_seed, uint64_t& known_change_seed)
{
    char input[64];
    printf("\n(supported formats: decimal or hexadecimal starting with 0x)\n");
    printf("[*] Please enter the value of RandomMainAbility_seed: ");
    if (fgets(input, sizeof(input), stdin)) {
        if (input[0] == '0' && (input[1] == 'x' || input[1] == 'X')) {
            known_random_seed = strtoull(input + 2, NULL, 16);
        }
        else {
            known_random_seed = strtoull(input, NULL, 10);
        }
    }
    printf("[*] Please enter the ChangeAbility_seed value: ");
    if (fgets(input, sizeof(input), stdin)) {
        if (input[0] == '0' && (input[1] == 'x' || input[1] == 'X')) {
            known_change_seed = strtoull(input + 2, NULL, 16);
        }
        else {
            known_change_seed = strtoull(input, NULL, 10);
        }
    }
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

int search_memory_region_by_seed(HANDLE hProcess, uint64_t start_addr, uint64_t end_addr,
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


