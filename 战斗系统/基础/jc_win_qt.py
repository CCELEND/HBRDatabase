
import types

from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top


def creat_jc_win(parent_frame):
    logo_path = "./help.ico"
    img_path = "./战斗系统/基础/基础.png"

    if is_win_open("基础", __name__):
        win_set_top("基础", __name__)
        return "break"

    jc_win_frame = creat_Toplevel("基础", 600, 840, 190, 120)
    set_window_icon(jc_win_frame, logo_path)
    win_open_manage(jc_win_frame, __name__)

    jc_image_viewer = ImageViewerWithScrollbar(jc_win_frame, 600, 840, img_path)

    jc_win_frame.mousePressEvent = lambda ev: win_set_top(jc_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(jc_win_frame, __name__, jc_image_viewer)
        event.accept()
    jc_win_frame.closeEvent = types.MethodType(on_close, jc_win_frame)

    return "break"
