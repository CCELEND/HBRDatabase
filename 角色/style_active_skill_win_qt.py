
from PyQt5.QtWidgets import QWidget, QGroupBox, QLabel, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt
from window_qt import MONO_FONT
from tools import not_letter

from canvas_events_qt import WrappedLabel
from 角色.style_combobox_win_qt import creat_lv_combo_lab, bind_lv_combo_lab
from 角色.style_active_skill_change_win_qt import creat_active_skill_change_frame, is_skill_change
from 角色.style_effect_win_qt import set_effect_frames

def creat_desc_frame(row_frame, desc_frame_row, active_skill):
    desc_frame = QWidget()
    desc_frame.setObjectName("desc_frame")
    desc_frame.setStyleSheet("background-color: transparent;")

    row_layout = row_frame.layout()
    if row_layout is not None:
        row_layout.addWidget(desc_frame, desc_frame_row, 0, 1, 4)

    desc_layout = QGridLayout(desc_frame)
    desc_layout.setSpacing(5)
    desc_layout.setContentsMargins(0, 0, 0, 5)
    desc_layout.setColumnStretch(0, 4)
    desc_layout.setColumnStretch(1, 1)
    desc_layout.setColumnStretch(2, 1)

    # desc_lab = WrappedLabel(active_skill.description)
    desc_lab = QLabel(active_skill.description)
    desc_lab.setObjectName("desc_frame_desc_lab")
    desc_lab.setFont(MONO_FONT)
    desc_layout.addWidget(desc_lab, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    text = ""
    for level_req in active_skill.level_reqs:
        text += "Lv" + level_req + " "
    level_req_lab = QLabel(text)
    level_req_lab.setFont(MONO_FONT)
    level_req_lab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    desc_layout.addWidget(level_req_lab, 0, 1, alignment=Qt.AlignRight | Qt.AlignVCenter)

    sp_cost_text = "SP" + active_skill.sp_cost if not_letter(active_skill.sp_cost) else active_skill.sp_cost
    uses_text = active_skill.max_uses if active_skill.max_uses else "∞"
    text = f"{sp_cost_text}\n{uses_text}"

    sp_use_lab = QLabel(text)
    sp_use_lab.setObjectName("desc_frame_sp_use_lab")
    sp_use_lab.setFont(MONO_FONT)
    sp_use_lab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    desc_layout.addWidget(sp_use_lab, 0, 2, alignment=Qt.AlignRight | Qt.AlignVCenter)

    desc_layout.setRowStretch(0, 1)
    desc_frame_sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    desc_frame_sp.setHeightForWidth(True)
    desc_frame.setSizePolicy(desc_frame_sp)

    return desc_frame

def creat_active_skill_frame(scrollbar_frame_obj, parent_frame, active_skill_frame_row, style):
    active_skill_frame = QGroupBox("主动技能 / 被动技能")
    active_skill_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(active_skill_frame)

    frame_layout = QGridLayout(active_skill_frame)
    frame_layout.setSpacing(5)
    frame_layout.setContentsMargins(10, 10, 10, 10)
    for col in range(4):
        frame_layout.setColumnStretch(col, 1)

    for i, active_skill in enumerate(style.active_skills):
        row_frame = QGroupBox(active_skill.name)
        row_frame.setFont(MONO_FONT)
        frame_layout.addWidget(row_frame, i, 0, 1, 4)

        row_layout = QGridLayout(row_frame)
        row_layout.setSpacing(5)
        row_layout.setContentsMargins(10, 10, 10, 10)
        for col in range(4):
            row_layout.setColumnStretch(col, 1)

        creat_desc_frame(row_frame, 0, active_skill)

        effect_frames_row = 1
        if is_skill_change(active_skill):
            show_effects = creat_active_skill_change_frame(scrollbar_frame_obj, row_frame, active_skill)
            effect_frames_row += 1
        else:
            show_effects = active_skill.effects

        effect_frames = QWidget()
        effect_frames.setObjectName("effect_frames")
        effect_frames.setStyleSheet("background-color: transparent;")
        effect_frames.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        row_layout.addWidget(effect_frames, effect_frames_row, 0, 1, 4)

        lv_combo_labs, lv_combo_texts = set_effect_frames(effect_frames, show_effects)

        lv_combo_row = effect_frames_row + 1
        lv_combo_lab_frame = QWidget()
        lv_combo_lab_frame.setObjectName("lv_combo_lab_frame")
        lv_combo_lab_frame.setStyleSheet("background-color: transparent;")
        lv_combo_lab_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        row_layout.addWidget(lv_combo_lab_frame, lv_combo_row, 0, 1, 4)

        lv_combo_layout = QGridLayout(lv_combo_lab_frame)
        lv_combo_layout.setSpacing(5)
        lv_combo_layout.setContentsMargins(0, 0, 0, 0)
        lv_combo_layout.setColumnStretch(0, 1)
        lv_combo_layout.setColumnStretch(1, 3)

        level_max = int(active_skill.level_max)
        lv_combo = creat_lv_combo_lab(lv_combo_lab_frame, level_max)
        bind_lv_combo_lab(lv_combo, lv_combo_labs, lv_combo_texts)

    return active_skill_frame
