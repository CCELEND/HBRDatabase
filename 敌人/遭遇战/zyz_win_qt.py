
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 遭遇战.zyz_info import zyzs, get_all_zyz_obj

zyzs_json = {}

def load_resources():
    global zyzs_json
    if zyzs_json:
        return
    zyzs_json = load_json("./敌人/遭遇战/zyz.json")


def bind_zyz_canvas(parent_frame, zyz, x, y):
    photo = get_pixmap(zyz.img_path, (128, 72))
    canvas = create_image_label(parent_frame, photo, 130, 130)
    canvas.setGeometry(20, 29, 130, 130)
    mouse_bind_canvas_events2(canvas)

    if zyz.guide_path:
        bind_canvas_events(canvas,
            creat_zyz_win, parent_frame=parent_frame,
            zyz=zyz)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_zyz_win(event, parent_frame, zyz):
    if is_win_open(zyz.name, __name__):
        win_set_top(zyz.name, __name__)
        return "break"

    zyz_win_frame = creat_Toplevel(zyz.name, 600, 840, 230, 110)
    set_window_icon(zyz_win_frame, zyz.logo_path)
    win_open_manage(zyz_win_frame, __name__)

    zyz_image_viewer = ImageViewerWithScrollbar(zyz_win_frame, 600, 840, zyz.guide_path)

    zyz_win_frame.mousePressEvent = lambda ev: win_set_top(zyz_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(zyz_win_frame, __name__, zyz_image_viewer)
        event.accept()
    zyz_win_frame.closeEvent = types.MethodType(on_close, zyz_win_frame)

    return "break"


def show_zyz_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_zyz_obj(zyzs_json)
    global zyzs

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
    for i, zyz_name in enumerate(zyzs):
        zyz = zyzs[zyz_name]

        zyz_frame = QGroupBox(zyz_name)
        frame_layout = QGridLayout(zyz_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_zyz_canvas(zyz_frame, zyz, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(zyz_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
