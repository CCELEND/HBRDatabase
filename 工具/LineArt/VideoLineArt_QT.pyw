# -*- coding: utf-8 -*-
"""视频转线稿工具的独立启动入口（双击即可运行）。"""
import os
import sys

# 把仓库根目录加到 sys.path，方便直接双击运行本文件
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from 工具.LineArt.VideoLineArt_QT import run_video_line_art

if __name__ == "__main__":
    run_video_line_art()
