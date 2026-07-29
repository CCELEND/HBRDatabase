
import subprocess
import os
from PyQt5.QtWidgets import QMessageBox
from tools import run_admin, is_admin

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def load_seed_tools():
    seed_tools_path = os.path.abspath("./工具/GetEntriesGUILocal/seed_tools/seed_tools.exe")

    if not os.path.exists(seed_tools_path):
        error_msg = f"seed_tools.exe 文件不存在：\n{seed_tools_path}"
        QMessageBox.critical(None, "文件缺失", error_msg)
        logger.error(error_msg)
        return

    try:
        if not is_admin():
            response = QMessageBox.question(
                None,
                "需要管理员权限",
                "启动该工具需要管理员权限，是否立即提升？",
                QMessageBox.Yes | QMessageBox.No
            )
            if response != QMessageBox.Yes:
                QMessageBox.information(None, "提示", "未获取管理员权限，seed_tools.exe 启动中止！")
                logger.warning("用户拒绝提升权限，seed_tools.exe 启动中止！")
                return
            else:
                run_admin()

        subprocess.Popen(
            seed_tools_path,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            stdout=None,
            stderr=None,
            stdin=None
        )
    except Exception as e:
        print(f"[-] {e}")
        logger.error(str(e))
