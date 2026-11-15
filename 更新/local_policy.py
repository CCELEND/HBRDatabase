# -*- coding: utf-8 -*-
"""客户端本地文件与可分发文件的边界。

这里集中定义“只属于当前机器、绝不能参与更新/修复”的路径规则。
客户端哈希、服务器响应过滤、修复下载和服务端哈希生成都应该使用同一套规则，
避免出现“客户端跳过、服务器却要求下载”的死循环（例如 config.ini）。
"""

from __future__ import annotations

import os
from typing import Iterable, Mapping

# 这些目录直接剪枝，不再递归遍历。既避免做无用哈希，也避免把本机数据上传。
HASH_SKIP_DIRS = frozenset({
    "venv",
    ".venv",
    ".git",
    ".vs",
    ".vscode",
    "__pycache__",
    "node_modules",
    "chrome_user_data",
    "chrome-win64",
    ".pytest_cache",
    "tests",
    "scripts",
    "1.7.0_0",
    "2.1.0_0",
})

# 精确匹配的路径（统一使用 /，且在比较时忽略大小写）。
LOCAL_ONLY_EXACT = frozenset({
    "./工具/GetEntriesGUILocal/config.ini",
    "./工具/GetEntriesGUILocal/index_equipments.xlsx",
    "./工具/GetEntriesGUILocal/index_wash_entries.xlsx",
    "./关于/client_file_hashes.json",
    "./关于/server_file_hashes.json",
})

LOCAL_ONLY_SUFFIXES = (
    ".mp3",
    ".flac",
    ".log",
    ".pyc",
    ".pyo",
    ".tmp",
    ".swp",
    ".bak",
    ".part",
)

# 只用于目录前缀的规则。注意不要包含“工具/HBR伤害模拟/”整个目录：
# 该目录下的 Load.py 和压缩包仍然需要分发，只有解压出来的版本目录是本地内容。
LOCAL_ONLY_PREFIXES = (
    "./音乐/下载/",
    "./工具/chrome/chrome-win64/",
    "./日志/",
)


def normalize_key(key: str | os.PathLike[str]) -> str:
    """把哈希键统一成 ``./a/b`` 形式，便于跨平台比较。"""
    text = os.fspath(key).replace("\\", "/").strip()
    if text.startswith("/"):
        text = "./" + text.lstrip("/")
    elif not text.startswith("./"):
        text = "./" + text.lstrip("./")
    return text


def is_local_only_path(key: str | os.PathLike[str]) -> bool:
    """判断某个相对路径是否属于本机文件、不参与更新/修复。"""
    normalized = normalize_key(key)
    folded = normalized.casefold()

    if folded in {item.casefold() for item in LOCAL_ONLY_EXACT}:
        return True

    parts = {part for part in folded.split("/") if part}
    if parts & HASH_SKIP_DIRS:
        return True

    if folded.endswith(LOCAL_ONLY_SUFFIXES):
        return True

    for prefix in LOCAL_ONLY_PREFIXES:
        if folded.startswith(prefix.casefold()):
            return True

    # HBR伤害模拟 的版本目录是运行时从 zip 解压出来的；
    # 同目录的 Load.py 和 *.zip 仍属于可分发内容。
    marker = "./工具/hbr伤害模拟/"
    if folded.startswith(marker):
        rest = folded[len(marker):]
        if "/" in rest and not rest.endswith(".zip"):
            return True

    return False


def filter_local_only_files(paths: Iterable[str]) -> list[str]:
    """从服务器返回的文件列表中剔除本机文件，保持原顺序。"""
    return [path for path in paths if not is_local_only_path(path)]


def filter_local_only_hashes(
        hashes: Mapping[str, str] | None) -> dict[str, str]:
    """从服务器哈希清单中剔除本机文件。"""
    if not hashes:
        return {}
    return {
        key: value for key, value in hashes.items()
        if not is_local_only_path(key)
    }
