# -*- coding: utf-8 -*-
"""「伤害分计算」的懒加载入口（点菜单时才加载对应窗口模块）。"""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def creat_dsc_win():
    """打开「伤害分计算」（Qt 版）。"""
    try:
        from 工具.DamageScoreCal.damage_score_cal_win_qt import creat_dsc_win as _f
        return _f()
    except Exception as e:
        logger.error("打开伤害分计算失败: %s", e)
        print(f"[-] {e}")


def creat_dsc_win_v2():
    """打开「伤害分计算V2」（Qt 版）。"""
    try:
        from 工具.DamageScoreCal.damage_score_cal_win_v2_qt import creat_dsc_win_v2 as _f
        return _f()
    except Exception as e:
        logger.error("打开伤害分计算V2失败: %s", e)
        print(f"[-] {e}")


def creat_dsc_win_tk():
    """打开「伤害分计算」（tk 版）。"""
    try:
        from 工具.DamageScoreCal.damage_score_cal_win import creat_dsc_win as _f
        return _f()
    except Exception as e:
        logger.error("打开伤害分计算失败(tk): %s", e)
        print(f"[-] {e}")


def creat_dsc_win_v2_tk():
    """打开「伤害分计算V2」（tk 版）。"""
    try:
        from 工具.DamageScoreCal.damage_score_cal_win_v2 import creat_dsc_win_v2 as _f
        return _f()
    except Exception as e:
        logger.error("打开伤害分计算V2失败(tk): %s", e)
        print(f"[-] {e}")
