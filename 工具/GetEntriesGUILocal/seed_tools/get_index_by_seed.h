#pragma once

#include "ProcessTreeNode_.h"


void get_RandomMainAbility_seed_ChangeAbility_seed(uint64_t& known_random_seed, uint64_t& known_change_seed);

int search_memory_region_by_seed(HANDLE hProcess, uint64_t start_addr, uint64_t end_addr,
    uint64_t known_random_seed, uint64_t known_change_seed);