# -*- coding: utf-8 -*-
"""服务器地址与 TLS（HTTPS）配置。

更新 / 音乐 / 修复 三处共用这一份配置，避免服务器地址散落在各个文件里。

默认使用 **https**。可用环境变量覆盖（不必改代码）：
    HBR_SERVER_SCHEME   https（默认）| http
    HBR_SERVER_HOST     47.96.235.36
    HBR_SERVER_PORT     65434        （更新 / 修复，服务端 HTTPS 端口）
    HBR_MUSIC_PORT      65432        （音乐，服务端 HTTPS 端口）
    HBR_SERVER_CA       服务端证书路径（推荐放入，用于校验服务器身份）

服务端「双栈」：明文 HTTP 仍保留在 65433 / 65431 供旧客户端使用，
HTTPS 在 65434 / 65432；因此这里默认走 https + 新端口。
若服务端还没配好证书，可临时设 HBR_SERVER_SCHEME=http、HBR_SERVER_PORT=65433
（音乐 HBR_MUSIC_PORT=65431）回到明文。

证书校验策略：
1. 若 ``HBR_SERVER_CA`` 指向的证书文件存在 → 用它校验（可防中间人攻击）；
2. 若使用 HTTPS 但找不到证书 → **直接拒绝请求**，不再静默关闭校验。

把服务端证书（自签名证书本身或签发它的 CA）保存为 ``./关于/server_ca.crt``
即可启用校验；服务端使用 ``SSL_CERT``/``SSL_KEY`` 指定的就是这张证书。

如果需要临时连接没有配置证书的开发服务器，必须显式地把 scheme 改为
``http``，而不是让 HTTPS 退化为“不校验证书”。
"""

import os

# 默认值
# 服务端「双栈」：明文 HTTP 仍留在 65433 / 65431（旧客户端用），
# HTTPS 在新端口 65434 / 65432 上（新客户端用）。
_DEFAULT_HOST = "47.96.235.36"
_DEFAULT_SCHEME = "https"
_DEFAULT_SERVER_PORT = 65434
_DEFAULT_MUSIC_PORT = 65432
_DEFAULT_CA_FILE = "./关于/server_ca.crt"

SCHEME = (os.getenv("HBR_SERVER_SCHEME", _DEFAULT_SCHEME) or "").strip().lower()
if SCHEME not in ("http", "https"):
    SCHEME = _DEFAULT_SCHEME
HOST = (os.getenv("HBR_SERVER_HOST", _DEFAULT_HOST) or "").strip() or _DEFAULT_HOST
SERVER_PORT = int(os.getenv("HBR_SERVER_PORT", str(_DEFAULT_SERVER_PORT)))
MUSIC_PORT = int(os.getenv("HBR_MUSIC_PORT", str(_DEFAULT_MUSIC_PORT)))
CA_FILE = os.getenv("HBR_SERVER_CA", _DEFAULT_CA_FILE)

class TLSConfigurationError(RuntimeError):
    """HTTPS 已启用，但客户端没有可用的服务器证书。"""


def server_url(port=None):
    """更新 / 修复 服务地址，例如 https://47.96.235.36:65433。"""
    return "%s://%s:%d" % (SCHEME, HOST, SERVER_PORT if port is None else port)


def music_url(port=None):
    """音乐 服务地址，例如 https://47.96.235.36:65431。"""
    return "%s://%s:%d" % (SCHEME, HOST, MUSIC_PORT if port is None else port)


def verify():
    """requests 的 verify 参数：HTTP 为 True，HTTPS 为 CA 路径。

    HTTPS 但 CA 文件缺失时抛错，绝不回退到 ``verify=False``。
    """
    if SCHEME != "https":
        return True
    if CA_FILE and os.path.isfile(CA_FILE):
        return CA_FILE
    raise TLSConfigurationError(
        "HTTPS 已启用，但找不到服务器证书文件：%s\n"
        "请把证书放到该路径，或显式设置 HBR_SERVER_SCHEME=http 使用明文开发服务器。"
        % (CA_FILE or "<未配置>"))


def requests_kwargs():
    """所有 HTTPS 请求都应带上的参数。

    不再关闭证书校验；证书缺失会在请求发出前直接失败。
    """
    return {"verify": verify()}
