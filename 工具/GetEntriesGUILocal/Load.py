# -*- coding: utf-8 -*-
"""「词条获取」的懒加载入口。

`get_entries_win_qt` 会 import pandas / openpyxl / lxml（实测约 0.5 秒），
放在这里让主界面启动时不去加载它，点菜单时才加载。
"""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def creat_ct_win():
    """打开「词条获取」窗口（Qt 版，HBRDatabaseGUI_QT）。"""
    try:
        from 工具.GetEntriesGUILocal.get_entries_win_qt import creat_ct_win as _f
        return _f()
    except Exception as e:
        logger.error("打开词条获取失败: %s", e)
        print(f"[-] {e}")


def creat_ct_win_tk():
    """打开「词条获取」窗口（tk 版，HBRDatabaseGUI）。"""
    try:
        from 工具.GetEntriesGUILocal.get_entries_win import creat_ct_win as _f
        return _f()
    except Exception as e:
        logger.error("打开词条获取失败(tk): %s", e)
        print(f"[-] {e}")
