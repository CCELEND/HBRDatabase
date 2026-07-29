
import os

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout, QVBoxLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import get_pixmap
from scrollbar_frame_qt import ScrollbarFrameWin


base_path = "./持有物/图片背景/ThumbnailBase.png"
halo_path = "./持有物/图片背景/ThumbnailHalo.png"


def _create_item_image_widget(parent, item_path, item_size=(80, 80)):
    widget = QWidget(parent)
    widget.setFixedSize(100, 100)

    base_label = QLabel(widget)
    base_pixmap = get_pixmap(base_path, (100, 100))
    base_label.setPixmap(base_pixmap)
    base_label.setGeometry(0, 0, 100, 100)

    halo_label = QLabel(widget)
    halo_pixmap = get_pixmap(halo_path, (96, 96))
    halo_label.setPixmap(halo_pixmap)
    halo_label.setGeometry(2, 2, 96, 96)

    item_label = QLabel(widget)
    item_pixmap = get_pixmap(item_path, item_size)
    item_label.setPixmap(item_pixmap)
    item_label.setGeometry(10, 10, item_size[0], item_size[1])

    return widget


def show_holding(parent_frame, data_dir):
    base_size = (100, 100)
    halo_size = (96, 96)
    item_size = (80, 80)

    base_pixmap = get_pixmap(base_path, base_size)
    halo_pixmap = get_pixmap(halo_path, halo_size)

    parent_layout = parent_frame.layout()
    if parent_layout is None:
        parent_layout = QVBoxLayout(parent_frame)
    parent_layout.setContentsMargins(10, 10, 10, 10)
    parent_layout.setSpacing(5)
    parent_layout.setAlignment(Qt.AlignTop)

    for i, item_name in enumerate(data_dir):
        item = data_dir[item_name]

        row_frame = QGroupBox(item_name)
        row_layout = QGridLayout(row_frame)
        row_layout.setContentsMargins(10, 10, 10, 10)
        row_layout.setSpacing(5)
        row_layout.setColumnStretch(0, 1)
        row_layout.setColumnStretch(1, 4)

        image_widget = _create_item_image_widget(row_frame, item["path"], item_size)
        row_layout.addWidget(image_widget, 0, 0, alignment=Qt.AlignCenter)

        info_frame = QWidget(row_frame)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(5)
        info_layout.setColumnStretch(0, 3)
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnStretch(2, 3)

        desc_label = QLabel(item["description"])
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(desc_label, 0, 0)

        price_label = QLabel(item["price"])
        price_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(price_label, 0, 1)

        location_label = QLabel(item["location"])
        location_label.setWordWrap(True)
        location_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(location_label, 0, 2)

        row_layout.addWidget(info_frame, 0, 1)
        parent_layout.addWidget(row_frame)

