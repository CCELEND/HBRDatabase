
import types

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from tools import get_list_not_isinstance_index
from 角色.style_effect_win_qt import delete_all_effect_frame, set_effect_frames
from 角色.style_combobox_win_qt import bind_lv_combo_lab

MONO_FONT = QFont("Monospace", 10, QFont.Bold)

SELECTED_STYLE = """
    QPushButton {
        background-color: #0078d7;
        color: white;
        border: 1px solid #0078d7;
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: bold;
        min-width: 60px;
    }
"""
UNSELECTED_STYLE = """
    QPushButton {
        background-color: rgba(255, 255, 255, 180);
        color: #0078d7;
        border: 1px solid #0078d7;
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: bold;
        min-width: 60px;
    }
    QPushButton:hover {
        background-color: rgba(224, 240, 248, 200);
    }
    QPushButton:pressed {
        background-color: rgba(208, 224, 240, 220);
    }
"""


def is_skill_change(active_skill) -> bool:
    if active_skill.switch:
        return True
    return False


def active_skill_change_proc(scrollbar_frame_obj, row_frame, change_effects_infos, active_skill):
    desc_index = get_list_not_isinstance_index(change_effects_infos)
    if desc_index is not None:
        desc = change_effects_infos[desc_index]
        sp_cost = change_effects_infos[desc_index + 1]
        max_uses = change_effects_infos[desc_index + 2]
        name = change_effects_infos[desc_index + 3]

        desc_frame = row_frame.findChild(QWidget, "desc_frame")
        if desc_frame is not None:
            desc_frame_desc_lab = desc_frame.findChild(QLabel, "desc_frame_desc_lab")
            if desc_frame_desc_lab is not None:
                desc_frame_desc_lab.setText(desc)
                desc_frame_desc_lab.updateGeometry()

            desc_frame_sp_use_lab = desc_frame.findChild(QLabel, "desc_frame_sp_use_lab")
            if desc_frame_sp_use_lab is not None and sp_cost:
                uses_text = max_uses if max_uses else "∞"
                text = f"SP{sp_cost}\n{uses_text}"
                desc_frame_sp_use_lab.setText(text)
                desc_frame_sp_use_lab.updateGeometry()

        if name:
            row_frame.setTitle(name)

    effect_frames = row_frame.findChild(QWidget, "effect_frames")
    if effect_frames is not None:
        row_frame.setUpdatesEnabled(False)
        try:
            delete_all_effect_frame(effect_frames)

            show_effects = []
            for effects_index in change_effects_infos[:desc_index]:
                show_effects.append(active_skill.effects[effects_index])

            lv_combo_labs, lv_combo_texts = set_effect_frames(effect_frames, show_effects)

            lv_combo_lab_frame = row_frame.findChild(QWidget, "lv_combo_lab_frame")
            if lv_combo_lab_frame is not None:
                lv_combo = lv_combo_lab_frame.findChild(QComboBox, "lv_combo")
                if lv_combo is not None:
                    bind_lv_combo_lab(lv_combo, lv_combo_labs, lv_combo_texts)
                    lv_combo.setCurrentText("Skill Lv.1")
        finally:
            row_frame.setUpdatesEnabled(True)
            row_frame.update()

    scrollbar_frame_obj.update_canvas()


class ChangeButtonManager:
    def __init__(self):
        self.current_button = None
        self.current_name = ""

    def handle_button_click(self, scrollbar_frame_obj, parent_frame, change_effects_infos,
                            active_skill, button, change_name):
        active_skill_change_proc(scrollbar_frame_obj, parent_frame, change_effects_infos, active_skill)

        if self.current_button is not None:
            self.current_button.setStyleSheet(UNSELECTED_STYLE)
            self.current_button.setChecked(False)

        button.setStyleSheet(SELECTED_STYLE)
        self.current_button = button
        self.current_name = change_name


def creat_active_skill_change_frame(scrollbar_frame_obj, parent_frame, active_skill) -> list:

    button_manager = ChangeButtonManager()

    change_button_frame = QWidget(parent_frame)
    change_button_frame.setObjectName("change_button_frame")
    change_button_frame.setStyleSheet("background-color: transparent;")

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(change_button_frame, 1, 0, 1, 4)

    button_layout = QHBoxLayout(change_button_frame)
    button_layout.setSpacing(10)
    button_layout.setContentsMargins(0, 5, 0, 5)

    default_change_name = ""
    buttons = []
    for i, change_name in enumerate(active_skill.switch):
        if not default_change_name:
            default_change_name = change_name

        change_effects_infos = active_skill.switch[change_name]

        change_button = QPushButton(change_name)
        change_button.setFont(MONO_FONT)
        change_button.setStyleSheet(UNSELECTED_STYLE)
        change_button.setCheckable(True)
        change_button.setCursor(Qt.PointingHandCursor)

        def make_command(cn=change_name, cei=change_effects_infos, btn=change_button):
            return lambda: button_manager.handle_button_click(
                scrollbar_frame_obj, parent_frame, cei, active_skill, btn, cn
            )

        change_button.clicked.connect(make_command())
        button_layout.addWidget(change_button)
        buttons.append(change_button)

    if buttons:
        buttons[0].setStyleSheet(SELECTED_STYLE)
        button_manager.current_button = buttons[0]
        button_manager.current_name = list(active_skill.switch.keys())[0]

    button_layout.addStretch()

    default_change_effects = []
    default_change_effects_infos = active_skill.switch[default_change_name]
    desc_index = get_list_not_isinstance_index(default_change_effects_infos)
    for default_effects_index in default_change_effects_infos[:desc_index]:
        default_change_effects.append(active_skill.effects[default_effects_index])

    return default_change_effects
