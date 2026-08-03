
from PyQt5.QtWidgets import QWidget, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt
from window_qt import MONO_FONT
from canvas_events_qt import get_pixmap, create_image_label, WrappedLabel, QLabel

from 角色.style_text import output_attack_skill, output_skill_effect
from 角色.style_info import is_skill_effect

import 战斗系统.属性.attributes_info
import 战斗系统.状态.status_info

def set_effect_frames(effect_frames, show_effects):
    main_effect_lv_combo_lab = []
    main_effect_lv_combo_text = []
    lv_combo_labs = []
    lv_combo_texts = []
    main_effect_flag = False

    for effect_frame_row, skill in enumerate(show_effects):
        desc_lab, text, is_attack_skill = creat_effect_frame(effect_frames, effect_frame_row, skill)
        if is_attack_skill:
            lv_combo_labs.append(desc_lab)
            lv_combo_texts.append(text)
        else:
            main_effect_lv_combo_lab.append(desc_lab)
            main_effect_lv_combo_text.append(text)
            if skill.main_effect:
                main_effect_flag = True

    if main_effect_flag or not lv_combo_labs:
        if main_effect_lv_combo_lab:
            lv_combo_labs.append(main_effect_lv_combo_lab[0])
            lv_combo_texts.append(main_effect_lv_combo_text[0])

    return lv_combo_labs, lv_combo_texts

def delete_all_effect_frame(effect_frames):
    layout = effect_frames.layout()
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

def delete_effect_frame(effect_frames, effect_frame_row):
    layout = effect_frames.layout()
    if layout is None:
        return
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if widget is not None:
            row, _, _, _ = layout.getItemPosition(i)
            if row == effect_frame_row:
                widget.deleteLater()
                return

def creat_effect_frame(effect_frames, effect_frame_row, skill):
    effect_frame = QWidget()
    effect_frame.setStyleSheet("background-color: transparent;")
    layout = QGridLayout(effect_frame)
    layout.setSpacing(5)
    layout.setContentsMargins(5, 0, 5, 5)

    is_attack_skill = False

    if is_skill_effect(skill):
        effect_path = 战斗系统.状态.status_info.status[skill.effect_type].path
        effect_pixmap = get_pixmap(effect_path, (60, 60))
        effect_label = create_image_label(effect_frame, effect_pixmap, 60, 60)
        layout.addWidget(effect_label, 0, 0, alignment=Qt.AlignCenter)

        text = output_skill_effect(skill.turn_num, skill.duration, skill.target, skill.effect_type,
            战斗系统.状态.status_info.status[skill.effect_type].description, skill.value, skill.attribute_multiplier,
            skill.attribute_difference,
            IsActive=True
        )
    else:
        weapon_attribute = skill.weapon_attribute
        if skill.element_attribute:
            attack_img_path = 战斗系统.属性.attributes_info.attributes[skill.element_attribute + weapon_attribute].path
        else:
            attack_img_path = 战斗系统.属性.attributes_info.attributes[weapon_attribute].path

        attack_pixmap = get_pixmap(attack_img_path, (60, 60))
        attack_label = create_image_label(effect_frame, attack_pixmap, 60, 60)
        layout.addWidget(attack_label, 0, 0, alignment=Qt.AlignCenter)

        text = output_attack_skill(skill.hit_num, skill.target, skill.hit_damage,
            skill.biased,
            skill.strength, skill.attribute_multiplier,
            skill.attribute_difference, skill.destructive_multiplier
        )
        is_attack_skill = True

    # 靠左上下居中
    # desc_lab = WrappedLabel(text)
    desc_lab = QLabel(text)
    desc_lab.setFont(MONO_FONT)
    layout.addWidget(desc_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    layout.setRowStretch(0, 1)

    effect_frame_sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    effect_frame_sp.setHeightForWidth(True)
    effect_frame.setSizePolicy(effect_frame_sp)

    effect_frames_layout = effect_frames.layout()
    if effect_frames_layout is None:
        effect_frames_layout = QGridLayout(effect_frames)
        effect_frames_layout.setSpacing(0)
        effect_frames_layout.setContentsMargins(0, 0, 0, 0)
    effect_frames_layout.addWidget(effect_frame, effect_frame_row, 0, 1, 1)
    effect_frames_layout.setRowStretch(effect_frame_row, 1)
    effect_frames_layout.setColumnStretch(0, 1)

    return desc_lab, text, is_attack_skill
