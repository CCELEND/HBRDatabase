
import types

from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top


def creat_od_win(parent_frame):
    logo_path = "./战斗系统/OD/OD.ico"
    img_path = "./战斗系统/OD/OD.png"

    if is_win_open("OD", __name__):
        win_set_top("OD", __name__)
        return "break"

    od_win_frame = creat_Toplevel("OD", 1100, 386, 330, 220)
    set_window_icon(od_win_frame, logo_path)
    win_open_manage(od_win_frame, __name__)

    od_image_viewer = ImageViewerWithScrollbar(od_win_frame, 1100, 386, img_path)

    od_win_frame.mousePressEvent = lambda ev: win_set_top(od_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(od_win_frame, __name__, od_image_viewer)
        event.accept()
    od_win_frame.closeEvent = types.MethodType(on_close, od_win_frame)

    return "break"
