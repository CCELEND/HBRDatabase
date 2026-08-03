
import queue
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer


error_queue = queue.Queue()
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
