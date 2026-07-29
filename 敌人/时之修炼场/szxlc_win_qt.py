
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 时之修炼场.szxlc_info import szxlcs, get_all_szxlc_obj

szxlcs_json = {}

def load_resources():
    global szxlcs_json
    if szxlcs_json:
        return
    szxlcs_json = load_json("./敌人/时之修炼场/szxlc.json")


def bind_szxlc_canvas(parent_frame, szxlc, x, y):
    photo = get_pixmap(szxlc.img_path, (90, 90))
    canvas = create_image_label(parent_frame, photo, 130, 130)
    canvas.setGeometry(20, 20, 130, 130)
    mouse_bind_canvas_events2(canvas)

    if szxlc.guide_path:
        bind_canvas_events(canvas,
            creat_szxlc_win, parent_frame=parent_frame,
            szxlc=szxlc)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_szxlc_win(event, parent_frame, szxlc):
    if is_win_open(szxlc.name, __name__):
        win_set_top(szxlc.name, __name__)
        return "break"

    szxlc_win_frame = creat_Toplevel(szxlc.name, 600, 840, 230, 110)
    set_window_icon(szxlc_win_frame, szxlc.logo_path)
    win_open_manage(szxlc_win_frame, __name__)

    szxlc_image_viewer = ImageViewerWithScrollbar(szxlc_win_frame, 600, 840, szxlc.guide_path)

    szxlc_win_frame.mousePressEvent = lambda ev: win_set_top(szxlc_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(szxlc_win_frame, __name__, szxlc_image_viewer)
        event.accept()
    szxlc_win_frame.closeEvent = types.MethodType(on_close, szxlc_win_frame)

    return "break"


def show_szxlc_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_szxlc_obj(szxlcs_json)
    global szxlcs

    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)
        for col in range(5):
            scroll_layout.setColumnStretch(col, 1)

    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    column_count = 0
    for i, szxlc_name in enumerate(szxlcs):
        szxlc = szxlcs[szxlc_name]

        szxlc_frame = QGroupBox(szxlc_name)
        frame_layout = QGridLayout(szxlc_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_szxlc_canvas(szxlc_frame, szxlc, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(szxlc_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
