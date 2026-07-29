import types
from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2, set_tooltip
from window_qt import set_window_icon_webp, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from 状态.status_info import get_all_statu_obj
import 状态.status_info


def bind_statu_canvas(parent_frame, statu, x, y):
    photo = get_pixmap(statu.path, (60, 60))
    canvas = create_image_label(parent_frame, photo, 60, 60)
    set_tooltip(canvas, statu.name)
    mouse_bind_canvas_events2(canvas)
    bind_canvas_events(canvas,
        creat_statu_win, parent_frame=parent_frame,
        statu=statu)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def creat_statu_win(event, parent_frame, statu):
    if is_win_open(statu.name, __name__):
        win_set_top(statu.name, __name__)
        return "break"

    statu_win_frame = creat_Toplevel(statu.name, 540, 200, 730, 350)
    set_window_icon_webp(statu_win_frame, statu.path)
    win_open_manage(statu_win_frame, __name__)

    statu_frame = QGroupBox(statu.name)
    statu_layout = QGridLayout(statu_frame)
    statu_layout.setContentsMargins(10, 10, 10, 10)
    statu_layout.setSpacing(5)
    statu_layout.setColumnStretch(0, 3)
    statu_layout.setColumnStretch(1, 1)

    info = statu.effect if statu.effect else statu.description
    info_label = QLabel(info)
    info_label.setWordWrap(True)
    info_label.setAlignment(Qt.AlignCenter)
    statu_layout.addWidget(info_label, 0, 0)

    stack_label = QLabel(statu.stack)
    stack_label.setAlignment(Qt.AlignCenter)
    statu_layout.addWidget(stack_label, 0, 1)

    central = statu_win_frame.centralWidget()
    layout = central.layout()
    if layout is None:
        layout = QGridLayout(central)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)
    layout.addWidget(statu_frame, 0, 0)

    def on_close(self, event):
        win_close_manage(statu_win_frame, __name__)
        event.accept()

    statu_win_frame.closeEvent = types.MethodType(on_close, statu_win_frame)

    return "break"


def set_frame_newline(frame, item_num, newline_num, column_count):
    row = item_num // newline_num
    column = item_num % newline_num
    parent_layout = frame.parentWidget().layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(frame, row, column)
    column_count += 1
    if column_count == newline_num:
        column_count = 0
    return column_count


def show_statu(scrollbar_frame_obj):
    get_all_statu_obj()
    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)
        for col in range(6):
            scroll_layout.setColumnStretch(col, 1)
    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    for type_num, type_name in enumerate(状态.status_info.statu_categories):
        type_frame = QGroupBox(type_name + "类型状态")
        type_layout = QGridLayout(type_frame)
        type_layout.setContentsMargins(10, 10, 10, 10)
        type_layout.setSpacing(5)
        type_layout.setAlignment(Qt.AlignTop)
        scroll_layout.addWidget(type_frame, type_num, 0, 1, 6)

        series_column_count = 0
        for series_num, series in enumerate(状态.status_info.statu_categories[type_name]):
            series_frame = QGroupBox(series)
            series_layout = QGridLayout(series_frame)
            series_layout.setContentsMargins(5, 5, 5, 5)
            series_layout.setSpacing(5)
            series_layout.setAlignment(Qt.AlignTop)

            statu_column_count = 0
            for statu_num, statu_name in enumerate(状态.status_info.statu_categories[type_name][series]):
                statu = 状态.status_info.statu_categories[type_name][series][statu_name]

                if len(状态.status_info.statu_categories[type_name][series]) == 1:
                    bind_statu_canvas(series_frame, statu, 0, 0)
                else:
                    statu_frame = QGroupBox(statu_name)
                    statu_frame_layout = QGridLayout(statu_frame)
                    statu_frame_layout.setContentsMargins(5, 5, 5, 5)
                    statu_frame_layout.setSpacing(5)
                    bind_statu_canvas(statu_frame, statu, 0, 0)

                    if type_name in ['增益', '减益', '其他', '异常']:
                        if series in ["技能效果强化", "对HP百分比伤害", "减益，异常移除", '强击破', 'EShield', '元素暴击伤害上升', '元素攻击上升', '元素暴击率上升', '连击数上升']:
                            statu_frame.setParent(series_frame)
                            statu_column_count = set_frame_newline(statu_frame, statu_num, 3, statu_column_count)
                        else:
                            statu_frame.setParent(series_frame)
                            statu_column_count = set_frame_newline(statu_frame, statu_num, 4, statu_column_count)
                    else:
                        series_layout.addWidget(statu_frame, 0, statu_num)

            if type_name in ['增益']:
                series_frame.setParent(type_frame)
                series_column_count = set_frame_newline(series_frame, series_num, 3, series_column_count)
            elif type_name in ['减益']:
                series_frame.setParent(type_frame)
                series_column_count = set_frame_newline(series_frame, series_num, 4, series_column_count)
            elif type_name in ['其他']:
                series_frame.setParent(type_frame)
                series_column_count = set_frame_newline(series_frame, series_num, 5, series_column_count)
            else:
                type_layout.addWidget(series_frame, 0, series_num)

    scrollbar_frame_obj.update_canvas()
    return "break"

