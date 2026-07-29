
import types

from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top


def creat_gmtf_win(parent_frame):
    logo_path = "./help.ico"
    img_path = "./战斗系统/共鸣天赋/共鸣天赋.png"

    if is_win_open("共鸣天赋", __name__):
        win_set_top("共鸣天赋", __name__)
        return "break"

    gmtf_win_frame = creat_Toplevel("共鸣天赋", 1300, 731, 190, 120)
    set_window_icon(gmtf_win_frame, logo_path)
    win_open_manage(gmtf_win_frame, __name__)

    gmtf_image_viewer = ImageViewerWithScrollbar(gmtf_win_frame, 1300, 731, img_path)

    gmtf_win_frame.mousePressEvent = lambda ev: win_set_top(gmtf_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(gmtf_win_frame, __name__, gmtf_image_viewer)
        event.accept()
    gmtf_win_frame.closeEvent = types.MethodType(on_close, gmtf_win_frame)

    return "break"
