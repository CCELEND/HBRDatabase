
from PyQt5.QtWidgets import QWidget, QGroupBox, QLabel, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from canvas_events_qt import get_pixmap, create_image_label, WrappedLabel
from tools import has_sublist
from 角色.style_info import AttackSkill, SkillEffect
from 角色.style_text import output_skill_effect, output_attack_skill

import 战斗系统.状态.status_info
import 战斗系统.属性.attributes_info

MONO_FONT = QFont("Monospace", 10, QFont.Bold)


def is_passive_skill_effect(passive_skill_effect_type: list):
    if not passive_skill_effect_type[0] in ["斩", "突", "打"]:
        return True
    return False


def creat_passive_effect_frame(effect_frames, effect_frame_row, passive_skill_effect_type: list):
    effect_frame = QWidget()
    effect_frame.setStyleSheet("background-color: transparent;")
    layout = QGridLayout(effect_frame)
    layout.setSpacing(5)
    layout.setContentsMargins(5, 0, 5, 5)

    if is_passive_skill_effect(passive_skill_effect_type):
        passive_skill_effect = SkillEffect.from_list(passive_skill_effect_type)
        effect_pixmap = get_pixmap(战斗系统.状态.status_info.status[passive_skill_effect.effect_type].path, (60, 60))
        effect_label = create_image_label(effect_frame, effect_pixmap, 60, 60)
        layout.addWidget(effect_label, 0, 0, alignment=Qt.AlignCenter)

        text = output_skill_effect(passive_skill_effect.turn_num, passive_skill_effect.duration,
            passive_skill_effect.target, passive_skill_effect.effect_type,
            战斗系统.状态.status_info.status[passive_skill_effect.effect_type].description,
            passive_skill_effect.value, passive_skill_effect.attribute_multiplier,
            passive_skill_effect.attribute_difference,
            IsActive=False
        )
    else:
        attack_skill = AttackSkill.from_list(passive_skill_effect_type)
        weapon_attribute = attack_skill.weapon_attribute
        if attack_skill.element_attribute:
            attack_img_path = 战斗系统.属性.attributes_info.attributes[attack_skill.element_attribute + weapon_attribute].path
        else:
            attack_img_path = 战斗系统.属性.attributes_info.attributes[weapon_attribute].path

        attack_pixmap = get_pixmap(attack_img_path, (60, 60))
        attack_label = create_image_label(effect_frame, attack_pixmap, 60, 60)
        layout.addWidget(attack_label, 0, 0, alignment=Qt.AlignCenter)

        text = output_attack_skill(attack_skill.hit_num, attack_skill.target, attack_skill.hit_damage,
            attack_skill.biased,
            attack_skill.strength, attack_skill.attribute_multiplier,
            attack_skill.attribute_difference, attack_skill.destructive_multiplier
        )

    # desc_lab = WrappedLabel(text)
    desc_lab = QLabel(text)
    desc_lab.setFont(MONO_FONT)
    layout.addWidget(desc_lab, 0, 1)

    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    layout.setRowStretch(0, 1)

    effect_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    effect_frames_layout = effect_frames.layout()
    if effect_frames_layout is None:
        effect_frames_layout = QGridLayout(effect_frames)
        effect_frames_layout.setSpacing(0)
        effect_frames_layout.setContentsMargins(0, 0, 0, 0)
    effect_frames_layout.addWidget(effect_frame, effect_frame_row, 0, 1, 1)
    effect_frames_layout.setRowStretch(effect_frame_row, 1)
    effect_frames_layout.setColumnStretch(0, 1)

    return desc_lab, text


def creat_passive_skill_frame(parent_frame, passive_skill_frame_row, style):
    passive_skill_frame = QGroupBox("天赋")
    passive_skill_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(passive_skill_frame)

    frame_layout = QGridLayout(passive_skill_frame)
    frame_layout.setSpacing(5)
    frame_layout.setContentsMargins(10, 10, 10, 10)
    for col in range(4):
        frame_layout.setColumnStretch(col, 1)

    for i, passive_skill in enumerate(style.passive_skills):
        row_frame = QGroupBox("[Auto]" + passive_skill.name)
        row_frame.setFont(MONO_FONT)
        frame_layout.addWidget(row_frame, i, 0, 1, 4)

        row_layout = QGridLayout(row_frame)
        row_layout.setSpacing(5)
        row_layout.setContentsMargins(10, 10, 10, 10)
        for col in range(4):
            row_layout.setColumnStretch(col, 1)

        # 描述 frame
        desc_frame = QWidget()
        desc_frame.setStyleSheet("background-color: transparent;")
        desc_layout = QGridLayout(desc_frame)
        desc_layout.setSpacing(5)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setColumnStretch(0, 4)
        desc_layout.setColumnStretch(1, 1)
        row_layout.addWidget(desc_frame, 0, 0, 1, 4)

        # desc_lab = WrappedLabel(passive_skill.description)
        desc_lab = QLabel(passive_skill.description)
        desc_lab.setFont(MONO_FONT)
        desc_layout.addWidget(desc_lab, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        lb_lab = QLabel("LB" + passive_skill.LB)
        lb_lab.setFont(MONO_FONT)
        lb_lab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        desc_layout.addWidget(lb_lab, 0, 1, alignment=Qt.AlignRight | Qt.AlignVCenter)

        desc_layout.setRowStretch(0, 1)
        desc_frame_sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        desc_frame_sp.setHeightForWidth(True)
        desc_frame.setSizePolicy(desc_frame_sp)

        # 技能效果 frame
        effect_frame = QWidget()
        effect_frame.setStyleSheet("background-color: transparent;")
        effect_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        effect_frame_layout = QGridLayout(effect_frame)
        effect_frame_layout.setSpacing(5)
        effect_frame_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(effect_frame, 1, 0, 1, 4)

        if not isinstance(passive_skill.effect_type, list):
            effect_frame_layout.setColumnStretch(0, 0)
            effect_frame_layout.setColumnStretch(1, 1)

            effect_pixmap = get_pixmap(战斗系统.状态.status_info.status[passive_skill.effect_type].path, (60, 60))
            effect_label = create_image_label(effect_frame, effect_pixmap, 60, 60)
            effect_frame_layout.addWidget(effect_label, 0, 0, alignment=Qt.AlignCenter)

            text = output_skill_effect(passive_skill.turn_num, passive_skill.duration, passive_skill.target,
                passive_skill.effect_type,
                战斗系统.状态.status_info.status[passive_skill.effect_type].description,
                passive_skill.value,
                IsActive=False
            )
            # effect_lab = WrappedLabel(text)
            effect_lab = QLabel(text)
            effect_lab.setFont(MONO_FONT)
            # effect_frame_layout.addWidget(effect_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
            #靠左垂直居中
            effect_frame_layout.addWidget(effect_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        else:
            effect_frame_layout.setColumnStretch(0, 1)
            if has_sublist(passive_skill.effect_type):
                for idx, passive_skill_effect_type in enumerate(passive_skill.effect_type):
                    creat_passive_effect_frame(effect_frame, idx, passive_skill_effect_type)
            else:
                creat_passive_effect_frame(effect_frame, 0, passive_skill.effect_type)

    return passive_skill_frame
