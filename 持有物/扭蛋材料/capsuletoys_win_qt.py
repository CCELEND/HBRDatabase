
from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import get_pixmap, mouse_bind_canvas_events2
from tools import load_json
import 持有物.holding_win_qt


capsuletoys_json = {}


def load_resources():
    global capsuletoys_json
    if capsuletoys_json:
        return
    capsuletoys_json = load_json("./持有物/扭蛋材料/capsuletoys.json")


def _create_capsuletoy_image_widget(parent, item_path):
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

    item_label = QLabel(widget)
    item_pixmap = get_pixmap(item_path, (80, 80))
    item_label.setPixmap(item_pixmap)
    item_label.setGeometry(10, 10, 80, 80)

    mouse_bind_canvas_events2(item_label)

    return widget


def show_capsuletoys(scrollbar_frame_obj):
    load_resources()
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
    for i, capsuletoy_name in enumerate(capsuletoys_json):
        item_photo_path = capsuletoys_json[capsuletoy_name]["path"]

        capsuletoy_frame = QGroupBox(capsuletoy_name)
        frame_layout = QGridLayout(capsuletoy_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(5)

        image_widget = _create_capsuletoy_image_widget(capsuletoy_frame, item_photo_path)
        frame_layout.addWidget(image_widget, 0, 0, alignment=Qt.AlignCenter)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(capsuletoy_frame, row, column)

        column_count += 1
        if column_count == 5:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"

