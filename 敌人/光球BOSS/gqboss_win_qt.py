
import types

from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 光球BOSS.gqboss_info import gqbosss, get_all_gqboss_obj

gqbosss_json = {}

def load_resources():
    global gqbosss_json
    if gqbosss_json:
        return
    gqbosss_json = load_json("./敌人/光球BOSS/gqboss.json")


def bind_gqboss_canvas(parent_frame, gqboss, x, y):
    photo = get_pixmap(gqboss.img_path, (149, 210))
    canvas = create_image_label(parent_frame, photo, 160, 210)
    canvas.setGeometry(20, 0, 160, 210)
    mouse_bind_canvas_events2(canvas)

    if gqboss.guide_path:
        bind_canvas_events(canvas,
            creat_gqboss_win, parent_frame=parent_frame,
            gqboss=gqboss)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_gqboss_win(event, parent_frame, gqboss):
    if is_win_open(gqboss.name, __name__):
        win_set_top(gqboss.name, __name__)
        return "break"

    gqboss_win_frame = creat_Toplevel(gqboss.name, 600, 840, 230, 110)
    set_window_icon(gqboss_win_frame, gqboss.logo_path)
    win_open_manage(gqboss_win_frame, __name__)

    gqboss_image_viewer = ImageViewerWithScrollbar(gqboss_win_frame, 600, 840, gqboss.guide_path)

    gqboss_win_frame.mousePressEvent = lambda ev: win_set_top(gqboss_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(gqboss_win_frame, __name__, gqboss_image_viewer)
        event.accept()
    gqboss_win_frame.closeEvent = types.MethodType(on_close, gqboss_win_frame)

    return "break"


def show_gqboss_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_gqboss_obj(gqbosss_json)
    global gqbosss

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
    for i, gqboss_name in enumerate(gqbosss):
        gqboss = gqbosss[gqboss_name]

        gqboss_frame = QGroupBox(gqboss_name)
        frame_layout = QGridLayout(gqboss_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_gqboss_canvas(gqboss_frame, gqboss, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(gqboss_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
