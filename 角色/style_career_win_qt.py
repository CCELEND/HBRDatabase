
from PyQt5.QtWidgets import QGroupBox, QGridLayout
from PyQt5.QtCore import Qt
from window_qt import MONO_FONT
from canvas_events_qt import get_pixmap, create_image_label, set_tooltip

import 战斗系统.职业.careers_info
import 战斗系统.属性.attributes_info

def _create_single_element_attribute(parent_frame, element_attribute, weapon_attribute, attributes_info):
    element_attribute_path = attributes_info[element_attribute].path
    element_attribute_pixmap = get_pixmap(element_attribute_path, (40, 40))
    element_attribute_label = create_image_label(parent_frame, element_attribute_pixmap, 60, 40)

    weapon_attribute_path = attributes_info[weapon_attribute].path
    weapon_attribute_pixmap = get_pixmap(weapon_attribute_path, (40, 40))
    weapon_attribute_label = create_image_label(parent_frame, weapon_attribute_pixmap, 60, 40)

    return element_attribute_label, weapon_attribute_label

def _create_double_element_attribute(parent_frame, element_attribute, weapon_attribute, attributes_info):
    element_attribute_path0 = attributes_info[element_attribute[0]].path
    element_attribute_pixmap0 = get_pixmap(element_attribute_path0, (40, 40))
    element_attribute_label0 = create_image_label(parent_frame, element_attribute_pixmap0, 60, 40)

    element_attribute_path1 = attributes_info[element_attribute[1]].path
    element_attribute_pixmap1 = get_pixmap(element_attribute_path1, (40, 40))
    element_attribute_label1 = create_image_label(parent_frame, element_attribute_pixmap1, 60, 40)

    weapon_attribute_path = attributes_info[weapon_attribute].path
    weapon_attribute_pixmap = get_pixmap(weapon_attribute_path, (40, 40))
    weapon_attribute_label = create_image_label(parent_frame, weapon_attribute_pixmap, 60, 40)

    return element_attribute_label0, element_attribute_label1, weapon_attribute_label

def _create_attribute_widgets(parent_frame, element_attribute, weapon_attribute):
    attributes_info = 战斗系统.属性.attributes_info.attributes
    if len(element_attribute) == 1:
        return _create_single_element_attribute(parent_frame, element_attribute, weapon_attribute, attributes_info)
    else:
        return _create_double_element_attribute(parent_frame, element_attribute, weapon_attribute, attributes_info)

def creat_career_frame(parent_frame, career_frame_row, style):
    element_attribute = style.element_attribute if style.element_attribute is not None else "无"
    weapon_attribute = style.weapon_attribute

    career = 战斗系统.职业.careers_info.careers[style.career]

    career_frame = QGroupBox(style.career + "-" + element_attribute + "-" + weapon_attribute)
    career_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(career_frame)

    layout = QGridLayout(career_frame)
    layout.setSpacing(5)
    layout.setContentsMargins(10, 10, 10, 10)

    career_pixmap = get_pixmap(career.path, (200, 40))
    career_label = create_image_label(career_frame, career_pixmap, 240, 40)
    layout.addWidget(career_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    attr_widgets = _create_attribute_widgets(career_frame, element_attribute, weapon_attribute)
    for col, widget in enumerate(attr_widgets, start=1):
        layout.addWidget(widget, 0, col, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    layout.setColumnStretch(len(attr_widgets) + 1, 1)

    return career_frame
