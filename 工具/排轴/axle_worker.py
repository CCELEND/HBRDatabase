# -*- coding: utf-8 -*-
"""后台生成轴图的 QThread。"""

from PyQt5.QtCore import QThread, pyqtSignal

# 持有运行中的 worker：窗口先关闭时不能让它被 Python 回收
_LIVE_WORKERS = set()


def keep_axle_worker(worker):
    _LIVE_WORKERS.add(worker)
    worker.finished.connect(lambda: _LIVE_WORKERS.discard(worker))


class _AxleImageWorker(QThread):
    """后台渲染轴图，避免长轴时卡死 UI。"""

    done = pyqtSignal(object, object)  # (QImage, error)

    def __init__(self, data, ds):
        super().__init__()
        self._data = data
        self._ds = ds

    def run(self):
        try:
            from 工具.排轴.axle_image import render_axle_image
            image = render_axle_image(self._data, ds=self._ds)
            self.done.emit(image, None)
        except Exception as e:
            self.done.emit(None, e)
