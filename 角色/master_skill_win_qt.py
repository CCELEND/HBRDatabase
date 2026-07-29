
import types

from PyQt5.QtWidgets import QWidget, QGroupBox, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from canvas_events_qt import get_pixmap, create_image_label
from canvas_events_qt import bind_canvas_events, mouse_bind_canvas_events2, set_tooltip
from window_qt import set_window_expand, creat_Toplevel, set_window_top, set_window_icon
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 角色.master_skill_info import MasterSkillEffect
from 角色.style_text import output_skill_effect, output_attack_skill
from 角色.team_info import get_team_logo_path
import 战斗系统.状态.status_info
import 战斗系统.属性.attributes_info

MONO_FONT = QFont("Monospace", 10, QFont.Bold)


def load_resources():
    战斗系统.状态.status_info.get_all_statu_obj()
    战斗系统.属性.attributes_info.get_all_attribute_obj()


def creat_desc_frame(row_frame, master_skill):
    desc_frame = QWidget()
    desc_layout = QGridLayout(desc_frame)
    desc_layout.setSpacing(5)
    desc_layout.setContentsMargins(0, 0, 0, 5)
    desc_layout.setColumnStretch(0, 4)
    desc_layout.setColumnStretch(1, 1)

    desc_lab = QLabel(master_skill.description)
    desc_lab.setFont(MONO_FONT)
    desc_lab.setWordWrap(True)
    desc_lab.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    desc_layout.addWidget(desc_lab, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

    if master_skill.max_uses:
        text = "SP" + master_skill.sp_cost + '\n' + master_skill.max_uses
    else:
        if master_skill.sp_cost == "被动技能":
            text = master_skill.sp_cost + '\n' + "∞"
        else:
            text = "SP" + master_skill.sp_cost + '\n' + "∞"
    sp_use_lab = QLabel(text)
    sp_use_lab.setFont(MONO_FONT)
    sp_use_lab.setAlignment(Qt.AlignRight | Qt.AlignTop)
    desc_layout.addWidget(sp_use_lab, 0, 1, alignment=Qt.AlignRight | Qt.AlignTop)

    row_layout = row_frame.layout()
    if row_layout is not None:
        row_layout.addWidget(desc_frame, 0, 0, 1, 4)

    return desc_frame


def creat_master_skill_frame(scrollbar_frame_obj, master_skill):
    scrollbar_frame_obj.destroy_components()

    parent_frame = scrollbar_frame_obj.scrollable_frame
    parent_layout = parent_frame.layout()
    if parent_layout is None:
        parent_layout = QGridLayout(parent_frame)
        parent_layout.setSpacing(10)
        parent_layout.setContentsMargins(10, 10, 10, 10)
        parent_layout.setAlignment(Qt.AlignTop)

    row_frame = QGroupBox(master_skill.name)
    row_frame.setFont(MONO_FONT)
    parent_layout.addWidget(row_frame, 0, 0, 1, 4)

    row_layout = QGridLayout(row_frame)
    row_layout.setSpacing(5)
    row_layout.setContentsMargins(10, 10, 10, 10)
    for col_index in range(4):
        row_layout.setColumnStretch(col_index, 1)

    creat_desc_frame(row_frame, master_skill)

    for j, skill in enumerate(master_skill.effects):
        effect_frame = QWidget()
        effect_layout = QGridLayout(effect_frame)
        effect_layout.setSpacing(5)
        effect_layout.setContentsMargins(0, 0, 0, 5)
        effect_layout.setColumnStretch(0, 1)
        effect_layout.setColumnStretch(1, 6)
        row_layout.addWidget(effect_frame, j + 1, 0, 1, 4)

        if isinstance(skill, MasterSkillEffect):
            effect_path = 战斗系统.状态.status_info.status[skill.effect_type].path
            effect_pixmap = get_pixmap(effect_path, (60, 60))
            effect_label = create_image_label(effect_frame, effect_pixmap, 60, 60)
            effect_layout.addWidget(effect_label, 0, 0, alignment=Qt.AlignCenter)

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
            effect_layout.addWidget(attack_label, 0, 0, alignment=Qt.AlignCenter)

            text = output_attack_skill(skill.hit_num, skill.target, skill.hit_damage,
                skill.biased,
                skill.strength, skill.attribute_multiplier,
                skill.attribute_difference, skill.destructive_multiplier
            )

        desc_lab = QLabel(text)
        desc_lab.setFont(MONO_FONT)
        desc_lab.setWordWrap(True)
        desc_lab.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        effect_layout.addWidget(desc_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

    missions_row = 1 + len(master_skill.effects)
    missions_lab = QLabel(master_skill.missions)
    missions_lab.setFont(MONO_FONT)
    missions_lab.setWordWrap(True)
    missions_lab.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    row_layout.addWidget(missions_lab, missions_row, 0, 1, 4, alignment=Qt.AlignLeft | Qt.AlignTop)

    return row_frame


def creat_master_skill_win(event, parent_frame, role):
    load_resources()

    master_skill = role.master_skill

    open_master_win = master_skill.name + f"—{role.name}"
    if is_win_open(open_master_win, __name__):
        win_set_top(open_master_win, __name__)
        return "break"

    master_win_frame = creat_Toplevel(open_master_win, 812, 300, 560, 510)
    set_window_expand(master_win_frame, rowspan=1, columnspan=2)
    set_window_icon(master_win_frame, get_team_logo_path(role.team))
    scrollbar_frame_obj = ScrollbarFrameWin(master_win_frame, columnspan=2)

    win_open_manage(master_win_frame, __name__)

    def on_close(self, event):
        win_close_manage(master_win_frame, __name__)
        event.accept()

    master_win_frame.closeEvent = types.MethodType(on_close, master_win_frame)

    creat_master_skill_frame(scrollbar_frame_obj, master_skill)

    return "break"
