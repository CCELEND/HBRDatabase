
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 棱镜战.ljz_info import ljzs, get_all_ljz_obj

ljzs_json = {}

def load_resources():
    global ljzs_json
    if ljzs_json:
        return
    ljzs_json = load_json("./敌人/棱镜战/ljz.json")


def bind_ljz_canvas(parent_frame, ljz, x, y):
    photo = get_pixmap(ljz.img_path, (128, 176))
    canvas = create_image_label(parent_frame, photo, 150, 176)
    canvas.setGeometry(60, 0, 150, 176)
    mouse_bind_canvas_events2(canvas)

    if ljz.guide_path:
        bind_canvas_events(canvas,
            creat_ljz_win, parent_frame=parent_frame,
            ljz=ljz)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_ljz_win(event, parent_frame, ljz):
    if is_win_open(ljz.name, __name__):
        win_set_top(ljz.name, __name__)
        return "break"

    ljz_win_frame = creat_Toplevel(ljz.name, 600, 840, 230, 110)
    set_window_icon(ljz_win_frame, ljz.logo_path)
    win_open_manage(ljz_win_frame, __name__)

    ljz_image_viewer = ImageViewerWithScrollbar(ljz_win_frame, 600, 840, ljz.guide_path)

    ljz_win_frame.mousePressEvent = lambda ev: win_set_top(ljz_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(ljz_win_frame, __name__, ljz_image_viewer)
        event.accept()
    ljz_win_frame.closeEvent = types.MethodType(on_close, ljz_win_frame)

    return "break"


def show_ljz_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_ljz_obj(ljzs_json)
    global ljzs

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
    for i, ljz_name in enumerate(ljzs):
        ljz = ljzs[ljz_name]

        ljz_frame = QGroupBox(ljz_name)
        frame_layout = QGridLayout(ljz_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_ljz_canvas(ljz_frame, ljz, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(ljz_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
