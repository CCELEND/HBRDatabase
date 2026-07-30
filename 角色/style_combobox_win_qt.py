
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from 角色.style_proc import on_attack_combo_select, on_buff_attack_combo_select
from 角色.style_proc import on_heal_combo_select
from 角色.style_proc import on_hit_combo_select, on_defense_combo_select, on_buff_combo_select
from 角色.style_proc import on_debuff_combo_select
from 角色.style_proc import on_mindeye_combo_select
from 角色.style_proc import on_percentage_combo_select

MONO_FONT = QFont("Monospace", 10, QFont.Bold)

skill_options = [
    "Skill Lv.1", "Skill Lv.2", "Skill Lv.3", "Skill Lv.4", "Skill Lv.5",
    "Skill Lv.6", "Skill Lv.7", "Skill Lv.8", "Skill Lv.9", "Skill Lv.10",
    "Skill Lv.11", "Skill Lv.12", "Skill Lv.13",
    "Skill Lv.14", "Skill Lv.15", "Skill Lv.16", "Skill Lv.17"
]


class _ComboEvent:
    def __init__(self, combo: QComboBox):
        self._combo = combo
        self.widget = self

    def get(self):
        return self._combo.currentText()


def creat_lv_combo_lab(parent_frame, level_max) -> QComboBox:
    lv_combo = QComboBox(parent_frame)
    lv_combo.setObjectName("lv_combo")
    lv_combo.addItems(skill_options[:level_max])
    lv_combo.setEditable(False)
    lv_combo.setCurrentText("Skill Lv.1")
    lv_combo.setFont(MONO_FONT)
    lv_combo.setCursor(Qt.PointingHandCursor)
    lv_combo.setStyleSheet("""
        QComboBox {
            padding: 6px 10px;
            border: 1px solid rgba(160, 160, 160, 180);
            border-radius: 6px;
            background-color: rgba(245, 245, 245, 230);
            color: #333333;
            min-width: 110px;
        }
        QComboBox:hover {
            border: 1px solid #0078d7;
            background-color: rgba(255, 255, 255, 240);
        }
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid rgba(160, 160, 160, 180);
            border-radius: 6px;
            background-color: rgba(245, 245, 245, 240);
            selection-background-color: #0078d7;
            selection-color: #ffffff;
            outline: none;
            padding: 4px;
        }
    """)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(lv_combo, 0, 0)

    return lv_combo


def bind_lv_combo_lab(lv_combo, lv_combo_labs, lv_combo_texts):
    def make_handler(handler, **kwargs):
        def wrapper():
            event = _ComboEvent(lv_combo)
            handler(event, **kwargs)
        return wrapper

    if "技能强度" in lv_combo_texts[0]:
        if len(lv_combo_texts) == 2:
            lv_combo.currentTextChanged.connect(
                make_handler(on_buff_attack_combo_select, desc_labs=lv_combo_labs, lv1_skill_strengths=lv_combo_texts)
            )
        else:
            lv_combo.currentTextChanged.connect(
                make_handler(on_attack_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
            )
    elif "回复DP" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_heal_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "防御上升" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_defense_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "连击数上升" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_hit_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "上升" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_buff_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "下降" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_debuff_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "心眼" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_mindeye_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "百分比的伤害" in lv_combo_texts[0]:
        lv_combo.currentTextChanged.connect(
            make_handler(on_percentage_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
