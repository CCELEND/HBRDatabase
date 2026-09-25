# -*- coding: utf-8 -*-
"""排轴 + OD 计算 工具入口。"""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def load_hbr_axle_od():
    """打开「排轴OD计算」窗口。"""
    try:
        from 工具.排轴.axle_od_win_qt import creat_axle_od_win
        return creat_axle_od_win()
    except Exception as e:
        logger.error("打开排轴OD计算失败: %s", e)
        print(f"[-] {e}")
