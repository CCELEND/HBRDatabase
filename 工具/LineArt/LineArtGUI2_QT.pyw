# -*- coding: utf-8 -*-
"""图片转线稿工具 2.0 的独立启动入口（双击即可运行）。

真正的界面代码在 LineArtGUI2_QT.py，这里只负责把仓库根目录加进
sys.path 并启动，避免同一份代码维护两遍。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from 工具.LineArt.LineArtGUI2_QT import run_LineArtGUI2_QT

if __name__ == "__main__":
    run_LineArtGUI2_QT()
