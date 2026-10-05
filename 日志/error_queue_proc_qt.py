
import queue
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer

# 与 tk 版**共用同一个队列**：tools 等模块出错时都是往
# 日志.error_queue_proc.error_queue 里放消息，这里必须读同一个队列，
# 否则错误消息会进到没人读的队列里，界面永远不弹提示。
from 日志.error_queue_proc import error_queue

_error_timer = None


def _has_visible_window(qapp):
    """检查是否还有可见的顶层窗口，避免关闭后弹出 QMessageBox 导致程序无法退出"""
    for w in qapp.topLevelWidgets():
        if w.isVisible() and not isinstance(w, QMessageBox):
            return True
    return False


def _show_queued_errors():
    qapp = QApplication.instance()
    if qapp is None or qapp.closingDown() or not _has_visible_window(qapp):
        return
    try:
        while not error_queue.empty():
            if qapp.closingDown() or not _has_visible_window(qapp):
                return
            error_msg = error_queue.get_nowait()
            QMessageBox.critical(None, "错误", error_msg)
    except queue.Empty:
        pass


def check_error_queue_qt(app):
    qapp = QApplication.instance()
    if qapp is None or qapp.closingDown():
        return

    _show_queued_errors()

    if qapp.closingDown():
        return

    global _error_timer
    if _error_timer is None:
        _error_timer = QTimer(qapp)
        _error_timer.timeout.connect(_show_queued_errors)
        qapp.aboutToQuit.connect(_error_timer.stop)
        qapp.lastWindowClosed.connect(_error_timer.stop)
    if not _error_timer.isActive():
        _error_timer.start(100)
