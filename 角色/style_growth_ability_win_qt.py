
from PyQt5.QtWidgets import QGroupBox, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from canvas_events_qt import get_pixmap, create_image_label

import 持有物.强化素材.strengthen_materials

MONO_FONT = QFont("Monospace", 10, QFont.Bold)


def creat_growth_ability_frame(parent_frame, growth_ability_frame_row, style):
    growth_ability_frame = QGroupBox("强化")
    growth_ability_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(growth_ability_frame)

    layout = QGridLayout(growth_ability_frame)
    layout.setSpacing(5)
    layout.setContentsMargins(10, 10, 10, 10)

    if style.element_attribute:
        if len(style.element_attribute) == 1:
            hoju_img_path = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
                f"宝珠（{style.element_attribute}属性）"]['path']
        else:
            hoju_img_path0 = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
                f"宝珠（{style.element_attribute[0]}属性）"]['path']
            hoju_img_path1 = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
                f"宝珠（{style.element_attribute[1]}属性）"]['path']
    else:
        hoju_img_path = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
            f"宝珠（{style.weapon_attribute}属性）"]['path']

    if not style.element_attribute or len(style.element_attribute) == 1:
        hoju_pixmap = get_pixmap(hoju_img_path, (80, 80))
        hoju_label = create_image_label(growth_ability_frame, hoju_pixmap, 80, 80)
        layout.addWidget(hoju_label, 0, 0, alignment=Qt.AlignCenter)

        text = style.growth_ability.description
        growth_ability_lab = QLabel(text)
        growth_ability_lab.setFont(MONO_FONT)
        growth_ability_lab.setWordWrap(True)
        growth_ability_lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(growth_ability_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
    else:
        hoju_pixmap0 = get_pixmap(hoju_img_path0, (80, 80))
        hoju_label0 = create_image_label(growth_ability_frame, hoju_pixmap0, 80, 80)
        layout.addWidget(hoju_label0, 0, 0, alignment=Qt.AlignCenter)

        hoju_pixmap1 = get_pixmap(hoju_img_path1, (80, 80))
        hoju_label1 = create_image_label(growth_ability_frame, hoju_pixmap1, 80, 80)
        layout.addWidget(hoju_label1, 0, 1, alignment=Qt.AlignCenter)

        text = style.growth_ability.description
        growth_ability_lab = QLabel(text)
        growth_ability_lab.setFont(MONO_FONT)
        growth_ability_lab.setWordWrap(True)
        growth_ability_lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(growth_ability_lab, 0, 2, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 1)

    return growth_ability_frame
