
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 高分挑战.gftz_info import gftzs, get_all_gftz_obj


gftzs_json = {}


def load_resources():
    global gftzs_json
    if gftzs_json:
        return
    gftzs_json = load_json("./敌人/高分挑战/gftz.json")


def bind_gftz_canvas(parent_frame, gftz, x, y):
    if "攻略" in gftz.name:
        photo = get_pixmap(gftz.img_path, (90, 90))
        label = create_image_label(parent_frame, photo, 130, 130)
        label.setGeometry(30, 20, 130, 130)
    else:
        photo = get_pixmap(gftz.img_path, (128, 72))
        label = create_image_label(parent_frame, photo, 130, 130)
        label.setGeometry(20, 29, 130, 130)
    mouse_bind_canvas_events2(label)

    if gftz.guide_path:
        bind_canvas_events(label, creat_gftz_win, parent_frame=parent_frame, gftz=gftz)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(label, x, y, alignment=Qt.AlignCenter)


def creat_gftz_win(event, parent_frame, gftz):
    if is_win_open(gftz.name, __name__):
        win_set_top(gftz.name, __name__)
        return "break"

    if "攻略" in gftz.name:
        gftz_win_frame = creat_Toplevel(gftz.name, 600, 840, 180, 140)
    else:
        gftz_win_frame = creat_Toplevel(gftz.name, 1280, 715, 180, 140)
    set_window_icon(gftz_win_frame, gftz.logo_path)
    win_open_manage(gftz_win_frame, __name__)

    gftz_image_viewer = ImageViewerWithScrollbar(gftz_win_frame, 1280, 715, gftz.guide_path)

    gftz_win_frame.mousePressEvent = lambda ev: win_set_top(gftz_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(gftz_win_frame, __name__, gftz_image_viewer)
        event.accept()
    gftz_win_frame.closeEvent = types.MethodType(on_close, gftz_win_frame)

    return "break"


def show_gftz_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_gftz_obj(gftzs_json)
    global gftzs

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
    for i, gftz_name in enumerate(gftzs):
        gftz = gftzs[gftz_name]

        gftz_frame = QGroupBox(gftz_name)
        frame_layout = QGridLayout(gftz_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_gftz_canvas(gftz_frame, gftz, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(gftz_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"

