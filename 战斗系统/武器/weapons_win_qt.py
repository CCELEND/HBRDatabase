
import types

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2, set_tooltip
from window_qt import set_window_icon_webp, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 武器.weapons_info import get_all_weapon_obj
import 武器.weapons_info


def bind_weapon_canvas(parent_frame, weapon, x, y):
    photo = get_pixmap(weapon.path, (60, 60))
    canvas = create_image_label(parent_frame, photo, 60, 60)
    set_tooltip(canvas, weapon.name)
    mouse_bind_canvas_events2(canvas)
    bind_canvas_events(canvas,
        creat_weapon_win, parent_frame=parent_frame,
        weapon=weapon)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_weapon_win(event, parent_frame, weapon):
    if is_win_open(weapon.name, __name__):
        win_set_top(weapon.name, __name__)
        return "break"

    weapon_win_frame = creat_Toplevel(weapon.name, 540, 200, 300, 280)
    set_window_icon_webp(weapon_win_frame, weapon.path)
    win_open_manage(weapon_win_frame, __name__)

    weapon_frame = QGroupBox(weapon.name)
    weapon_layout = QGridLayout(weapon_frame)
    weapon_layout.setContentsMargins(10, 10, 10, 10)
    weapon_layout.setSpacing(5)

    weapon_layout.setColumnStretch(0, 3)
    weapon_layout.setColumnStretch(1, 1)
    desc_label = QLabel(weapon.description)
    desc_label.setWordWrap(True)
    desc_label.setAlignment(Qt.AlignCenter)
    weapon_layout.addWidget(desc_label, 0, 0)
    hit_label = QLabel(weapon.hit)
    hit_label.setAlignment(Qt.AlignCenter)
    weapon_layout.addWidget(hit_label, 0, 1)

    central = weapon_win_frame.centralWidget()
    layout = central.layout()
    if layout is None:
        layout = QGridLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    layout.addWidget(weapon_frame, 0, 0)

    weapon_win_frame.mousePressEvent = lambda ev: win_set_top(weapon_win_frame, __name__)
    weapon_win_frame.closeEvent = lambda ev: (win_close_manage(weapon_win_frame, __name__), ev.accept())

    return "break"


def show_weapon(scrollbar_frame_obj):
    get_all_weapon_obj()
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
    for item_num, item_name in enumerate(武器.weapons_info.weapons):
        item = weapons.weapons_info.weapons[item_name]

        item_frame = QGroupBox(item_name)
        frame_layout = QGridLayout(item_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_weapon_canvas(item_frame, item, 0, 0)

        row = item_num // 3
        column = item_num % 3
        scroll_layout.addWidget(item_frame, row, column)

        column_count += 1
        if column_count == 3:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
