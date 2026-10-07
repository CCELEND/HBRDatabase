# -*- coding: utf-8 -*-
"""「风格图鉴获取」的懒加载入口。

`HBRbrochure` 会 import selenium（还有 urllib3 等一堆依赖），
放在这里让主界面启动时不去加载它。
"""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def get_hbr_brochure():
    """打开「风格图鉴获取」（Qt / tk 两个入口共用）。"""
    try:
        from 工具.HBRbrochure.HBRbrochure import get_hbr_brochure as _f
        return _f()
    except Exception as e:
        logger.error("打开风格图鉴获取失败: %s", e)
        print(f"[-] {e}")
