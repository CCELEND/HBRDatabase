#pragma once

#include "ProcessTreeNode_.h"

int search_memory_region(HANDLE hProcess, uint64_t start_addr, uint64_t end_addr);
