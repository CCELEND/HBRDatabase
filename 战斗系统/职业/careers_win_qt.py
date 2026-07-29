
import types

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2, set_tooltip
from window_qt import set_window_icon_webp, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 职业.careers_info import get_all_career_obj
import 职业.careers_info


def bind_career_canvas(parent_frame, career, x, y):
    photo = get_pixmap(career.path, (200, 40))
    canvas = create_image_label(parent_frame, photo, 240, 40)
    set_tooltip(canvas, career.name)
    mouse_bind_canvas_events2(canvas)
    bind_canvas_events(canvas,
        creat_career_win, parent_frame=parent_frame,
        career=career)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_career_win(event, parent_frame, career):
    if is_win_open(career.name, __name__):
        win_set_top(career.name, __name__)
        return "break"

    career_win_frame = creat_Toplevel(career.name, 540, 200, 300, 280)
    set_window_icon_webp(career_win_frame, career.path)
    win_open_manage(career_win_frame, __name__)

    career_frame = QGroupBox(career.name)
    career_layout = QGridLayout(career_frame)
    career_layout.setContentsMargins(10, 10, 10, 10)
    career_layout.setSpacing(5)

    desc_label = QLabel(career.description)
    desc_label.setWordWrap(True)
    desc_label.setAlignment(Qt.AlignCenter)
    career_layout.addWidget(desc_label, 0, 0)

    central = career_win_frame.centralWidget()
    layout = central.layout()
    if layout is None:
        layout = QGridLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    layout.addWidget(career_frame, 0, 0)

    # 正确关闭事件
    def on_close(ev):
        win_close_manage(career_win_frame, __name__)
        ev.accept()
    career_win_frame.closeEvent = on_close

    return "break"


def show_career(scrollbar_frame_obj):
    get_all_career_obj()
    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(5)
        scroll_layout.setAlignment(Qt.AlignTop)
        for col in range(3):
            scroll_layout.setColumnStretch(col, 1)

    column_count = 0
    for item_num, item_name in enumerate(职业.careers_info.careers):
        item = 职业.careers_info.careers[item_name]

        item_frame = QGroupBox(item_name)
        frame_layout = QGridLayout(item_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_career_canvas(item_frame, item, 0, 0)

        row = item_num // 3
        column = item_num % 3
        scroll_layout.addWidget(item_frame, row, column)

        column_count += 1
        if column_count == 3:
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"
