#pragma once
#include <windows.h>
#include <stdio.h>
#include <tlhelp32.h>
#include <iostream>
#include <vector>
#include <sstream>
#include <string>
#include <cstdio>
#include <regex>

PVOID GetMainHeapBase(DWORD pid);

BOOL IsRunAsAdmin();
void RequestAdminRights();



