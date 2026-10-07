# -*- coding: utf-8 -*-
"""把 ffmpeg.exe 压缩进项目，供「视频转线稿」自带使用。

生成（都在本目录下）：
    ffmpeg.exe.gz        压缩后的 ffmpeg（原版一百多 MB，压完约 60MB）
    ffmpeg_info.json     版本 / 大小 / sha256，客户端靠它判断本地缓存是否还有效

用法：
    python 工具/LineArt/ffmpeg/pack_ffmpeg.py                 # 自动找 PATH 里的 ffmpeg
    python 工具/LineArt/ffmpeg/pack_ffmpeg.py D:/ffmpeg/ffmpeg.exe

换版本时：先下新版 ffmpeg 替换掉旧的，再跑一次本脚本，然后把
ffmpeg.exe.gz 和 ffmpeg_info.json 同步到服务器即可（客户端会自动重新解压）。
"""
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "ffmpeg.exe.gz")
INFO = os.path.join(HERE, "ffmpeg_info.json")


def sha256_of(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def find_source():
    if len(sys.argv) > 1:
        return sys.argv[1]
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    # 常见位置兜底
    for cand in (r"F:\tool\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",):
        if os.path.exists(cand):
            return cand
    return ""


def main():
    src = find_source()
    if not src or not os.path.exists(src):
        print("找不到 ffmpeg.exe，请把路径作为参数传进来：")
        print("    python %s D:/ffmpeg/ffmpeg.exe" % os.path.relpath(__file__))
        return 1
    print("源文件:", src)

    out = subprocess.run([src, "-hide_banner", "-version"], capture_output=True)
    first = out.stdout.decode("utf-8", "replace").splitlines()
    first = first[0] if first else ""
    m = re.search(r"ffmpeg version (\S+)", first)
    version = m.group(1) if m else "unknown"
    print("版本:", version)

    raw_size = os.path.getsize(src)
    exe_sha = sha256_of(src)
    print("原始: %d 字节 (%.1f MB)" % (raw_size, raw_size / 1048576))

    t = time.time()
    tmp = DST + ".part"
    with open(src, "rb") as fin:
        with gzip.GzipFile(tmp, "wb", compresslevel=9, mtime=0) as fout:
            shutil.copyfileobj(fin, fout, 1024 * 1024)
    os.replace(tmp, DST)
    gz_size = os.path.getsize(DST)
    print("压缩: %d 字节 (%.1f MB)  压缩率 %.0f%%  用时 %.1fs"
          % (gz_size, gz_size / 1048576, gz_size / raw_size * 100, time.time() - t))

    info = {
        "name": "ffmpeg.exe",
        "version": version,
        "source": "https://github.com/BtbN/FFmpeg-Builds "
                  "(ffmpeg-master-latest-win64-gpl)",
        "license": "GPL v3 (含 libx264 / ffnvcodec / libvpl)",
        "raw_size": raw_size,
        "exe_sha256": exe_sha,
        "gz_sha256": sha256_of(DST),
    }
    with open(INFO, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print("已写入", os.path.basename(INFO))

    # 回读校验，确保压缩包是好的
    verify = os.path.join(HERE, "_verify_tmp.exe")
    with gzip.open(DST, "rb") as fin, open(verify, "wb") as fout:
        shutil.copyfileobj(fin, fout, 1024 * 1024)
    ok = sha256_of(verify) == exe_sha and os.path.getsize(verify) == raw_size
    os.remove(verify)
    print("回读校验:", "通过" if ok else "失败！")
    if not ok:
        return 1
    print("\n下一步：把 ffmpeg.exe.gz 和 ffmpeg_info.json 同步到服务器。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
