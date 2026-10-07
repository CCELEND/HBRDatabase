# -*- coding: utf-8 -*-
"""「音乐」窗口的懒加载入口。

音乐播放器会 import pygame / numpy（实测约 0.28 秒，pygame 还会往控制台
打一行欢迎信息），放在这里让主界面启动时不去加载它。
"""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def creat_music_win():
    """打开「音乐」窗口（Qt 版，HBRDatabaseGUI_QT）。"""
    try:
        from 音乐.music_win_qt import creat_music_win as _f
        return _f()
    except Exception as e:
        logger.error("打开音乐窗口失败: %s", e)
        print(f"[-] {e}")


def creat_music_win_tk():
    """打开「音乐」窗口（tk 版，HBRDatabaseGUI）。"""
    try:
        from 音乐.music_win import creat_music_win as _f
        return _f()
    except Exception as e:
        logger.error("打开音乐窗口失败(tk): %s", e)
        print(f"[-] {e}")
