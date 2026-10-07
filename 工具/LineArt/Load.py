# -*- coding: utf-8 -*-
"""图片 / 视频转线稿 工具的懒加载入口。

放在这里是为了让主界面启动时不要去 import cv2 / numpy，
只有真正点开对应工具时才加载（启动更快）。
"""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def load_LineArtGUI2_QT():
    """打开「图片转线稿工具 2.0」。"""
    try:
        from 工具.LineArt.LineArtGUI2_QT import load_LineArtGUI2_QT as _load
        return _load()
    except Exception as e:
        logger.error("打开图片转线稿工具失败: %s", e)
        print(f"[-] {e}")


def load_video_line_art():
    """打开「视频转线稿」。"""
    try:
        from 工具.LineArt.VideoLineArt_QT import load_video_line_art as _load
        return _load()
    except Exception as e:
        logger.error("打开视频转线稿失败: %s", e)
        print(f"[-] {e}")
