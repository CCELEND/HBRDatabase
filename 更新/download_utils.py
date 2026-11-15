# -*- coding: utf-8 -*-
"""更新/修复共用的安全下载实现。

每个文件先写入同目录的临时文件，流式下载完成后校验服务器提供的
SHA-256，再用 ``os.replace`` 原子替换目标文件。这样网络中断、取消或
哈希不匹配时都不会破坏已有的旧文件。
"""

from __future__ import annotations

import os
import re
import tempfile
from typing import Callable, Optional, Protocol
from urllib.parse import quote

from tools import safe_relative_path
from 更新.hash import calculate_file_hash_block
from 更新.server_config import requests_kwargs


class DownloadCancelled(Exception):
    """用户取消了下载。"""


class DownloadError(RuntimeError):
    """服务器返回错误、网络错误或文件完整性校验失败。"""


class _Response(Protocol):
    status_code: int
    headers: dict

    def iter_content(self, chunk_size: int = 8192): ...
    def close(self): ...


_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def expected_hash_for(server_file_hashes, file_name: str) -> Optional[str]:
    """按服务器原始键取期望哈希，兼容 ./ 前缀和反斜杠差异。"""
    if not server_file_hashes:
        return None
    normalized = file_name.replace("\\", "/")
    candidates = (
        file_name,
        normalized,
        "./" + normalized.lstrip("./"),
        normalized.lstrip("./"),
    )
    for candidate in candidates:
        if candidate in server_file_hashes:
            return server_file_hashes[candidate]
    # 大小写不同的服务器键很少见，但 Windows 文件名本身不区分大小写。
    folded = normalized.casefold()
    for key, value in server_file_hashes.items():
        if str(key).replace("\\", "/").casefold() == folded:
            return value
    return None


def download_file(
    server_url: str,
    file_name: str,
    *,
    base_dir: str = ".",
    expected_hash: Optional[str] = None,
    require_hash: bool = False,
    cancel_check: Optional[Callable[[], bool]] = None,
    progress_hook: Optional[Callable[[int, int], None]] = None,
    response_hook: Optional[Callable[[_Response | None], None]] = None,
) -> str:
    """下载一个文件，校验后原子替换。

    Args:
        server_url: 更新服务器根地址。
        file_name: 服务器清单中的相对路径。
        base_dir: 程序根目录，默认当前工作目录。
        expected_hash: 服务器清单中的 SHA-256。
        require_hash: 为 True 时缺少/格式错误的哈希会直接拒绝下载。
        cancel_check: 每个数据块之间调用，返回 True 时取消。
        progress_hook: ``(已下载字节, 总字节)``，总大小未知时为 0。
        response_hook: 拿到/释放 HTTP 响应时回调，用于窗口关闭时打断阻塞请求。

    Returns:
        目标文件的绝对路径。

    Raises:
        DownloadCancelled: 用户取消。
        DownloadError: 下载、校验或替换失败。
    """
    expected = (expected_hash or "").strip().lower()
    if expected and not _SHA256_RE.match(expected):
        raise DownloadError("服务器返回的文件哈希格式无效：%s" % file_name)
    if require_hash and not expected:
        raise DownloadError("服务器未提供文件哈希，已拒绝下载：%s" % file_name)

    if cancel_check and cancel_check():
        raise DownloadCancelled()

    # 路径只允许落在程序目录内，防止服务器清单被篡改后越界写入。
    safe_path = safe_relative_path(file_name, base_dir)
    target_dir = os.path.dirname(safe_path)
    os.makedirs(target_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        prefix=".hbr-download-", suffix=".part", dir=target_dir)
    os.close(fd)

    import requests

    try:
        encoded_name = quote(file_name)
        url = f"{server_url}/download/{encoded_name}"
        with requests.get(
                url, stream=True, timeout=(10, 60), **requests_kwargs()) as response:
            if response_hook:
                response_hook(response)
            try:
                if response.status_code != 200:
                    try:
                        error_msg = response.json().get("error", "未知错误")
                    except Exception:
                        error_msg = f"HTTP {response.status_code}"
                    raise DownloadError(str(error_msg))

                total_size = int(response.headers.get("content-length", 0) or 0)
                downloaded = 0
                with open(temp_path, "wb") as output:
                    for chunk in response.iter_content(chunk_size=8192):
                        if cancel_check and cancel_check():
                            raise DownloadCancelled()
                        if chunk:
                            output.write(chunk)
                            downloaded += len(chunk)
                            if progress_hook:
                                progress_hook(downloaded, total_size)
            finally:
                if response_hook:
                    response_hook(None)

        actual = calculate_file_hash_block(temp_path, file_name)[1].lower()
        if expected and actual != expected:
            raise DownloadError(
                "文件哈希校验失败：%s\n期望：%s\n实际：%s"
                % (file_name, expected, actual))

        os.replace(temp_path, safe_path)
        return safe_path
    except Exception:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        raise
