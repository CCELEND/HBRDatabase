
import os

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout, QVBoxLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label, ClickableLabel
from canvas_events_qt import mouse_bind_canvas_events2, set_tooltip
from window_qt import set_window_expand, set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

import 持有物.holding_win_qt
from 饰品.jewelrys_info import get_jewelrys_obj, load_type_resources
import 饰品.jewelrys_info
from 饰品.光球.orbs_skill_win_qt import creat_orb_skill_win


def _create_jewelry_image_widget(parent, jewelry):
    widget = QWidget(parent)
    widget.setFixedSize(100, 100)

    base_label = QLabel(widget)
    base_pixmap = get_pixmap(持有物.holding_win_qt.base_path, (100, 100))
    base_label.setPixmap(base_pixmap)
    base_label.setGeometry(0, 0, 100, 100)

    halo_label = QLabel(widget)
    halo_pixmap = get_pixmap(持有物.holding_win_qt.halo_path, (96, 96))
    halo_label.setPixmap(halo_pixmap)
    halo_label.setGeometry(2, 2, 96, 96)

    jewelry_label = QLabel(widget)
    jewelry_pixmap = get_pixmap(jewelry.path, (80, 80))
    jewelry_label.setPixmap(jewelry_pixmap)
    jewelry_label.setGeometry(10, 10, 80, 80)

    if jewelry.type == "光球":
        jewelry_label = ClickableLabel(widget)
        jewelry_label.setFixedSize(80, 80)
        jewelry_label.setGeometry(10, 10, 80, 80)
        if not jewelry_pixmap.isNull():
            jewelry_label.setPixmap(jewelry_pixmap)
        jewelry_label.setAlignment(Qt.AlignCenter)
        mouse_bind_canvas_events2(jewelry_label)
        bind_canvas_events(jewelry_label, creat_orb_skill_win, parent_frame=parent, orb=jewelry)

    return widget


def show_jewelrys(scrollbar_frame_obj, jewelrys):
    scrollbar_frame_obj.destroy_components()

    parent_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if parent_layout is None:
        parent_layout = QVBoxLayout(scrollbar_frame_obj.scrollable_frame)
    parent_layout.setContentsMargins(0, 0, 0, 0)
    parent_layout.setSpacing(5)
    parent_layout.setAlignment(Qt.AlignTop)

    for i, jewelry_name in enumerate(jewelrys):
        jewelry = jewelrys[jewelry_name]

        row_frame = QGroupBox(jewelry.name)
        row_layout = QGridLayout(row_frame)
        row_layout.setContentsMargins(10, 10, 10, 10)
        row_layout.setSpacing(5)
        row_layout.setColumnStretch(0, 1)
        row_layout.setColumnStretch(1, 5)

        image_widget = _create_jewelry_image_widget(row_frame, jewelry)
        row_layout.addWidget(image_widget, 0, 0, alignment=Qt.AlignCenter)

        info_frame = QWidget(row_frame)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(5)
        info_layout.setColumnStretch(0, 4)
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnStretch(2, 2)

        desc_label = QLabel(jewelry.description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(desc_label, 0, 0)

        rarity_label = QLabel(int(jewelry.rarity) * "★")
        rarity_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(rarity_label, 0, 1)

        location_label = QLabel(jewelry.location)
        location_label.setWordWrap(True)
        location_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(location_label, 0, 2)

        row_layout.addWidget(info_frame, 0, 1)
        parent_layout.addWidget(row_frame)

    scrollbar_frame_obj.update_canvas()


def bind_jewelry_type_canvas(parent_frame, jewelry_type_json, x, y):
    pixmap = get_pixmap(jewelry_type_json['img_path'], (60, 60))
    label = create_image_label(parent_frame, pixmap, 60, 60)
    set_tooltip(label, jewelry_type_json['name'])
    mouse_bind_canvas_events2(label)
    bind_canvas_events(label, creat_jewelrys_win, parent_frame=parent_frame, jewelry_type_json=jewelry_type_json)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(label, x, y, alignment=Qt.AlignCenter)


def creat_jewelrys_win(event, parent_frame, jewelry_type_json):
    jewelry_win_name = jewelry_type_json['name']

    if is_win_open(jewelry_win_name, __name__):
        win_set_top(jewelry_win_name, __name__)
        return "break"

    jewelrys = get_jewelrys_obj(jewelry_type_json)

    jewelry_win_frame = creat_Toplevel(jewelry_win_name, 1040, 800, 240, 80)
    logo_path = jewelry_type_json['logo_path']
    set_window_icon(jewelry_win_frame, logo_path)
    set_window_expand(jewelry_win_frame, rowspan=1, columnspan=2)

    win_open_manage(jewelry_win_frame, __name__)

    scrollbar_frame_obj = ScrollbarFrameWin(jewelry_win_frame, columnspan=2)
    show_jewelrys(scrollbar_frame_obj, jewelrys)

    jewelry_win_frame.mousePressEvent = lambda ev: win_set_top(jewelry_win_frame, __name__)
    jewelry_win_frame.closeEvent = lambda ev: (win_close_manage(jewelry_win_frame, __name__), ev.accept())

    return "break"


def show_jewelrys_type(scrollbar_frame_obj):
    load_type_resources()
    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)

        for col in range(4):
            scroll_layout.setColumnStretch(col, 1)

    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    jewelry_type_column_count = 0
    for jewelry_type_num, jewelry_type_name in enumerate(饰品.jewelrys_info.jewelrys_type_json):
        jewelry_type_json = 饰品.jewelrys_info.jewelrys_type_json[jewelry_type_name]

        jewelry_type_frame = QGroupBox(jewelry_type_name)
        frame_layout = QVBoxLayout(jewelry_type_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(5)

        bind_jewelry_type_canvas(jewelry_type_frame, jewelry_type_json, 0, 0)

        jewelry_type_row = jewelry_type_num // 4
        jewelry_type_column = jewelry_type_num % 4
        scroll_layout.addWidget(jewelry_type_frame, jewelry_type_row, jewelry_type_column)

        jewelry_type_column_count += 1
        if jewelry_type_column_count == 4:
            jewelry_type_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"

