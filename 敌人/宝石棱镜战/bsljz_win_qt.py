
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 宝石棱镜战.bsljz_info import bsljzs, get_all_bsljz_obj

bsljzs_json = {}

def load_resources():
    global bsljzs_json
    if bsljzs_json:
        return
    bsljzs_json = load_json("./敌人/宝石棱镜战/bsljz.json")


def bind_bsljz_canvas(parent_frame, bsljz, x, y):
    photo = get_pixmap(bsljz.img_path, (128, 176))
    canvas = create_image_label(parent_frame, photo, 150, 176)
    canvas.setGeometry(35, 0, 150, 176)
    mouse_bind_canvas_events2(canvas)

    if bsljz.guide_path:
        bind_canvas_events(canvas,
            creat_bsljz_win, parent_frame=parent_frame,
            bsljz=bsljz)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_bsljz_win(event, parent_frame, bsljz):
    if is_win_open(bsljz.name, __name__):
        win_set_top(bsljz.name, __name__)
        return "break"

    bsljz_win_frame = creat_Toplevel(bsljz.name, 600, 840, 230, 110)
    set_window_icon(bsljz_win_frame, bsljz.logo_path)
    win_open_manage(bsljz_win_frame, __name__)

    bsljz_image_viewer = ImageViewerWithScrollbar(bsljz_win_frame, 600, 840, bsljz.guide_path)

    bsljz_win_frame.mousePressEvent = lambda ev: win_set_top(bsljz_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(bsljz_win_frame, __name__, bsljz_image_viewer)
        event.accept()
    bsljz_win_frame.closeEvent = types.MethodType(on_close, bsljz_win_frame)

    return "break"


def show_bsljz_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_bsljz_obj(bsljzs_json)
    global bsljzs

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
    for i, bsljz_name in enumerate(bsljzs):
        bsljz = bsljzs[bsljz_name]

        bsljz_frame = QGroupBox(bsljz_name)
        frame_layout = QGridLayout(bsljz_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_bsljz_canvas(bsljz_frame, bsljz, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(bsljz_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
