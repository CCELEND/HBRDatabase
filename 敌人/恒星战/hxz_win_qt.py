
import types

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from canvas_events_qt import ImageViewerWithScrollbar
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 恒星战.hxz_info import hxzs, get_all_hxz_obj


base_path = "./敌人/恒星战/dimensionClassFrameL.png"

hxzs_json = {}


def load_resources():
    global hxzs_json
    if hxzs_json:
        return
    hxzs_json = load_json("./敌人/恒星战/hxz.json")


def creat_hxz_win(event, parent_frame, hxz):
    if is_win_open(hxz.name, __name__):
        win_set_top(hxz.name, __name__)
        return "break"

    if "攻略" in hxz.name:
        hxz_win_frame = creat_Toplevel(hxz.name, 600, 840, 180, 140)
    else:
        hxz_win_frame = creat_Toplevel(hxz.name, 1280, 720, 180, 140)
    set_window_icon(hxz_win_frame, hxz.logo_path)
    win_open_manage(hxz_win_frame, __name__)

    hxz_image_viewer = ImageViewerWithScrollbar(hxz_win_frame, 1280, 720, hxz.guide_path)

    hxz_win_frame.mousePressEvent = lambda ev: win_set_top(hxz_win_frame, __name__)
    def on_close(self, event):
        win_close_manage(hxz_win_frame, __name__, hxz_image_viewer)
        event.accept()
    hxz_win_frame.closeEvent = types.MethodType(on_close, hxz_win_frame)

    return "break"


def show_hxz_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_hxz_obj(hxzs_json)
    global hxzs

    base_size = (100, 100)
    enemy_size = (86, 86)
    base_pixmap = get_pixmap(base_path, base_size)

    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)

        for col in range(3):
            scroll_layout.setColumnStretch(col, 1)

    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    column_count = 0
    for i, hxz_name in enumerate(hxzs):
        hxz = hxzs[hxz_name]

        hxz_frame = QGroupBox(hxz_name)
        frame_layout = QGridLayout(hxz_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        photo = get_pixmap(hxz.img_path, (128, 72))
        label = create_image_label(hxz_frame, photo, 130, 130)
        label.setGeometry(20, 29, 130, 130)
        frame_layout.addWidget(label, 0, 0, alignment=Qt.AlignCenter)

        base_label = create_image_label(hxz_frame, base_pixmap, 130, 130)
        base_label.setGeometry(0, 15, 130, 130)
        enemy_photo = get_pixmap(hxz.img_path_enemy, enemy_size)
        enemy_label = QLabel(base_label)
        enemy_label.setPixmap(enemy_photo)
        enemy_label.setGeometry(22, 22, enemy_size[0], enemy_size[1])
        mouse_bind_canvas_events2(base_label)
        if hxz.guide_path:
            bind_canvas_events(base_label, creat_hxz_win, parent_frame=hxz_frame, hxz=hxz)
        frame_layout.addWidget(base_label, 0, 1, alignment=Qt.AlignCenter)

        row = i // 3
        column = i % 3
        scroll_layout.addWidget(hxz_frame, row, column)

        column_count += 1
        if column_count == 3:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"

