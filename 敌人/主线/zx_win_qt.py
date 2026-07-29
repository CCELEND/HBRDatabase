
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 主线.zx_info import zxs, get_all_zx_obj

zxs_json = {}

def load_resources():
    global zxs_json
    if zxs_json:
        return
    zxs_json = load_json("./敌人/主线/zx.json")


def bind_zx_canvas(parent_frame, zx, x, y):
    photo = get_pixmap(zx.img_path, (90, 90))
    canvas = create_image_label(parent_frame, photo, 130, 130)
    canvas.setGeometry(20, 20, 130, 130)
    mouse_bind_canvas_events2(canvas)

    if zx.guide_path:
        bind_canvas_events(canvas,
            creat_zx_win, parent_frame=parent_frame,
            zx=zx)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_zx_win(event, parent_frame, zx):
    if is_win_open(zx.name, __name__):
        win_set_top(zx.name, __name__)
        return "break"

    zx_win_frame = creat_Toplevel(zx.name, 600, 840, 230, 110)
    set_window_icon(zx_win_frame, zx.logo_path)
    win_open_manage(zx_win_frame, __name__)

    zx_image_viewer = ImageViewerWithScrollbar(zx_win_frame, 600, 840, zx.guide_path)

    zx_win_frame.mousePressEvent = lambda ev: win_set_top(zx_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(zx_win_frame, __name__, zx_image_viewer)
        event.accept()
    zx_win_frame.closeEvent = types.MethodType(on_close, zx_win_frame)

    return "break"


def show_zx_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_zx_obj(zxs_json)
    global zxs

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
    for i, zx_name in enumerate(zxs):
        zx = zxs[zx_name]

        zx_frame = QGroupBox(zx_name)
        frame_layout = QGridLayout(zx_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_zx_canvas(zx_frame, zx, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(zx_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
