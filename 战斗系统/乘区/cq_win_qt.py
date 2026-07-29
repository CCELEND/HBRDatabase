
import types

from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top


def creat_cq_win(parent_frame):
    logo_path = "./战斗系统/乘区/乘区.ico"
    img_path = "./战斗系统/乘区/乘区.png"

    if is_win_open("乘区", __name__):
        win_set_top("乘区", __name__)
        return "break"

    cq_win_frame = creat_Toplevel("乘区", 820, 500, 330, 220)
    set_window_icon(cq_win_frame, logo_path)
    win_open_manage(cq_win_frame, __name__)

    cq_image_viewer = ImageViewerWithScrollbar(cq_win_frame, 820, 500, img_path)

    cq_win_frame.mousePressEvent = lambda ev: win_set_top(cq_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(cq_win_frame, __name__, cq_image_viewer)
        event.accept()
    cq_win_frame.closeEvent = types.MethodType(on_close, cq_win_frame)

    return "break"
