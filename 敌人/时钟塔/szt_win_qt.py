
import types

from PyQt5.QtWidgets import QLabel, QWidget, QGroupBox, QGridLayout, QHBoxLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label
from canvas_events_qt import mouse_bind_canvas_events2
from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 时钟塔.szt_info import szts, get_all_szt_obj

from 战斗系统.属性.attributes_info import get_all_attribute_obj
import 战斗系统.属性.attributes_info


szts_json = {}


def load_resources():
    global szts_json
    if szts_json:
        return
    szts_json = load_json("./敌人/时钟塔/szt.json")


def bind_szt_canvas(parent_frame, szt, x, y):
    photo = get_pixmap(szt.img_path, (72, 72))
    canvas = create_image_label(parent_frame, photo, 90, 90)
    canvas.setGeometry(40, 9, 90, 90)
    mouse_bind_canvas_events2(canvas)
    bind_canvas_events(canvas, creat_szt_win, parent_frame=parent_frame, szt=szt)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(canvas, x, y, alignment=Qt.AlignCenter)


def extract_compound_attributes(s):
    base_elements = {'火', '冰', '雷', '光', '暗', '无', '斩', '突', '打'}

    parts = [part.strip() for part in s.split('、')]
    result = {}

    for part in parts:
        sign_pos = None
        for i, char in enumerate(part):
            if char in '+-':
                sign_pos = i
                break

        if sign_pos is None:
            result[part] = None
            continue

        attr_part = part[:sign_pos]
        value = int(part[sign_pos:])

        elements = []
        for elem in base_elements:
            if elem in attr_part:
                elements.append(elem)

        if elements:
            for elem in elements:
                result[elem] = value
        else:
            result[attr_part] = value

    return result


def _create_attribute_widget(parent, attribute_name, value, up_photo, down_photo):
    widget = QWidget(parent)
    widget.setFixedSize(50, 70)

    attribute = 战斗系统.属性.attributes_info.attributes[attribute_name]
    attribute_photo = get_pixmap(attribute.path, (40, 40))

    attr_label = create_image_label(widget, attribute_photo, 50, 40)
    attr_label.setGeometry(0, 0, 50, 40)

    arrow_label = QLabel(widget)
    arrow_label.setPixmap(up_photo if value < 0 else down_photo)
    arrow_label.setGeometry(25, 20, 20, 20)

    value_label = QLabel(str(value), widget)
    value_label.setAlignment(Qt.AlignCenter)
    value_label.setGeometry(0, 45, 50, 20)

    return widget


def creat_attributes_img_value(info_frame, attribute_value_dir, up_photo, down_photo):
    layout = info_frame.layout()
    if layout is None:
        layout = QHBoxLayout(info_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignLeft)

    for i, attribute_name in enumerate(attribute_value_dir):
        if not attribute_name:
            break
        value = attribute_value_dir[attribute_name]
        widget = _create_attribute_widget(info_frame, attribute_name, value, up_photo, down_photo)
        layout.addWidget(widget, alignment=Qt.AlignCenter)


def creat_szt_win(event, parent_frame, szt):
    if is_win_open(szt.name, __name__):
        win_set_top(szt.name, __name__)
        return "break"

    szt_win_frame = creat_Toplevel(szt.name, x=200, y=250)
    set_window_icon(szt_win_frame, szt.logo_path)
    win_open_manage(szt_win_frame, __name__)

    up_photo = get_pixmap("./战斗系统/状态/IconUp.webp", (20, 20))
    down_photo = get_pixmap("./战斗系统/状态/IconDown.webp", (20, 20))

    central = szt_win_frame.centralWidget()
    layout = central.layout()
    if layout is None:
        layout = QGridLayout(central)

    for col_index in range(4):
        layout.setColumnStretch(col_index, 1)

    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

    for i, enemy in enumerate(szt.enemys):
        row_frame = QGroupBox(enemy.name)
        row_layout = QGridLayout(row_frame)
        row_layout.setContentsMargins(10, 10, 10, 10)
        row_layout.setSpacing(5)
        row_layout.setColumnStretch(0, 1)
        row_layout.setColumnStretch(1, 6)

        enemy_photo = get_pixmap(enemy.img_path, (72, 72))
        enemy_label = create_image_label(row_frame, enemy_photo, 72, 72)
        row_layout.addWidget(enemy_label, 0, 0, alignment=Qt.AlignCenter)

        info_frame = QWidget(row_frame)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(5)
        info_layout.setColumnStretch(0, 2)
        info_layout.setColumnStretch(1, 3)
        info_layout.setColumnStretch(2, 3)
        info_layout.setColumnStretch(3, 3)
        info_layout.setColumnStretch(4, 3)

        border_label = QLabel("属性：" + enemy.border)
        border_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(border_label, 0, 0)

        dp_label = QLabel("DP：" + enemy.DP)
        dp_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(dp_label, 0, 1)

        hp_label = QLabel("HP：" + enemy.HP)
        hp_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(hp_label, 0, 2)

        weakness_frame = QWidget(info_frame)
        weakness_layout = QHBoxLayout(weakness_frame)
        weakness_layout.setContentsMargins(0, 0, 0, 0)
        weakness_layout.setSpacing(2)
        weakness_layout.setAlignment(Qt.AlignLeft)
        weakness_label = QLabel("弱点：")
        weakness_layout.addWidget(weakness_label)
        weakness_info_frames = QWidget(weakness_frame)
        weakness_layout.addWidget(weakness_info_frames)
        info_layout.addWidget(weakness_frame, 0, 3)

        attribute_value_dir = extract_compound_attributes(enemy.weakness)
        creat_attributes_img_value(weakness_info_frames, attribute_value_dir, up_photo, down_photo)

        resist_frame = QWidget(info_frame)
        resist_layout = QHBoxLayout(resist_frame)
        resist_layout.setContentsMargins(0, 0, 0, 0)
        resist_layout.setSpacing(2)
        resist_layout.setAlignment(Qt.AlignLeft)
        resist_label = QLabel("抗性：")
        resist_layout.addWidget(resist_label)
        resist_info_frames = QWidget(resist_frame)
        resist_layout.addWidget(resist_info_frames)
        info_layout.addWidget(resist_frame, 0, 4)

        attribute_value_dir = extract_compound_attributes(enemy.resist)
        creat_attributes_img_value(resist_info_frames, attribute_value_dir, up_photo, down_photo)

        row_layout.addWidget(info_frame, 0, 1)
        layout.addWidget(row_frame, i, 0, 1, 4)

    szt_win_frame.mousePressEvent = lambda ev: win_set_top(szt_win_frame, __name__)
    szt_win_frame.closeEvent = lambda ev: (win_close_manage(szt_win_frame, __name__), ev.accept())

    def on_close(self, event):
        win_close_manage(szt_win_frame, __name__)
        event.accept()

    szt_win_frame.closeEvent = types.MethodType(on_close, szt_win_frame)

    return "break"


def show_szt_enemys(scrollbar_frame_obj):
    load_resources()
    get_all_attribute_obj()
    get_all_szt_obj(szts_json)
    global szts

    scrollbar_frame_obj.destroy_components()

    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)
        for col in range(4):
            scroll_layout.setColumnStretch(col, 1)
            
    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    for i, szt_name in enumerate(szts):
        szt = szts[szt_name]
        enemy = szt.enemys[0]

        szt_frame = QGroupBox(enemy.name + "#" + szt_name)
        frame_layout = QGridLayout(szt_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)

        bind_szt_canvas(szt_frame, szt, 0, 0)

        row = i // 4
        column = i % 4
        scroll_layout.addWidget(szt_frame, row, column)

    scrollbar_frame_obj.update_canvas()
    return "break"

