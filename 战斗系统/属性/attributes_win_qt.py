
import types

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2, set_tooltip
from window_qt import set_window_icon_webp, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 属性.attributes_info import get_all_attribute_obj
import 属性.attributes_info


def bind_attribute_canvas(parent_frame, attribute, x, y):
    photo = get_pixmap(attribute.path, (60, 60))
    canvas = create_image_label(parent_frame, photo, 60, 60)
    set_tooltip(canvas, attribute.name)
    mouse_bind_canvas_events2(canvas)
    bind_canvas_events(canvas,
        creat_attribute_win, parent_frame=parent_frame,
        attribute=attribute)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_attribute_win(event, parent_frame, attribute):
    if is_win_open(attribute.name, __name__):
        win_set_top(attribute.name, __name__)
        return "break"

    attribute_win_frame = creat_Toplevel(attribute.name, 540, 200, 300, 280)
    set_window_icon_webp(attribute_win_frame, attribute.path)
    win_open_manage(attribute_win_frame, __name__)

    attribute_frame = QGroupBox(attribute.name)
    attribute_layout = QGridLayout(attribute_frame)
    attribute_layout.setContentsMargins(10, 10, 10, 10)
    attribute_layout.setSpacing(5)

    info_label = QLabel(attribute.description)
    info_label.setWordWrap(True)
    info_label.setAlignment(Qt.AlignCenter)
    attribute_layout.addWidget(info_label, 0, 0)

    central = attribute_win_frame.centralWidget()
    layout = central.layout()
    if layout is None:
        layout = QGridLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    layout.addWidget(attribute_frame, 0, 0)

    # 正确关闭事件
    def on_close(ev):
        win_close_manage(attribute_win_frame, __name__)
        ev.accept()
    attribute_win_frame.closeEvent = on_close

    return "break"



def show_attribute(scrollbar_frame_obj):
    get_all_attribute_obj()
    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)
        for col in range(4):
            scroll_layout.setColumnStretch(col, 1)

    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    column_count = 0
    for item_num, item_name in enumerate(属性.attributes_info.attributes):
        item = attributes.attributes_info.attributes[item_name]

        item_frame = QGroupBox(item_name)
        frame_layout = QGridLayout(item_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_attribute_canvas(item_frame, item, 0, 0)

        row = item_num // 4
        column = item_num % 4
        scroll_layout.addWidget(item_frame, row, column)

        column_count += 1
        if column_count == 4:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
