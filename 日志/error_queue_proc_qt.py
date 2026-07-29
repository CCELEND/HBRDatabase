
import queue
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer


error_queue = queue.Queue()
_error_timer = None


def _show_queued_errors():
    qapp = QApplication.instance()
    if qapp is None or qapp.closingDown():
        return
    try:
        while not error_queue.empty():
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
    if not _error_timer.isActive():
        _error_timer.start(100)
