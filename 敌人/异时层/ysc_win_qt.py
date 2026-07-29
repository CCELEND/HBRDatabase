
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 异时层.ysc_info import yscs, get_all_ysc_obj

yscs_json = {}

def load_resources():
    global yscs_json
    if yscs_json:
        return
    yscs_json = load_json("./敌人/异时层/yscs.json")


def bind_ysc_canvas(parent_frame, ysc, x, y):
    photo = get_pixmap(ysc.img_path, (90, 90))
    canvas = create_image_label(parent_frame, photo, 130, 130)
    canvas.setGeometry(20, 20, 130, 130)
    mouse_bind_canvas_events2(canvas)

    if ysc.guide_path:
        bind_canvas_events(canvas,
            creat_ysc_win, parent_frame=parent_frame,
            ysc=ysc)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_ysc_win(event, parent_frame, ysc):
    if is_win_open(ysc.name, __name__):
        win_set_top(ysc.name, __name__)
        return "break"

    ysc_win_frame = creat_Toplevel(ysc.name, 600, 840, 230, 110)
    set_window_icon(ysc_win_frame, ysc.logo_path)
    win_open_manage(ysc_win_frame, __name__)

    ysc_image_viewer = ImageViewerWithScrollbar(ysc_win_frame, 600, 840, ysc.guide_path)

    ysc_win_frame.mousePressEvent = lambda ev: win_set_top(ysc_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(ysc_win_frame, __name__, ysc_image_viewer)
        event.accept()
    ysc_win_frame.closeEvent = types.MethodType(on_close, ysc_win_frame)

    return "break"


def show_ysc_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_ysc_obj(yscs_json)
    global yscs

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
    for i, ysc_name in enumerate(yscs):
        ysc = yscs[ysc_name]

        ysc_frame = QGroupBox(ysc_name)
        frame_layout = QGridLayout(ysc_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_ysc_canvas(ysc_frame, ysc, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(ysc_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
