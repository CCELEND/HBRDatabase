
from PyQt5.QtWidgets import QComboBox, QSizePolicy
from PyQt5.QtCore import Qt
from window_qt import MONO_FONT
from 角色.style_proc import on_attack_combo_select, on_buff_attack_combo_select
from 角色.style_proc import on_heal_combo_select
from 角色.style_proc import on_hit_combo_select, on_defense_combo_select, on_buff_combo_select
from 角色.style_proc import on_debuff_combo_select
from 角色.style_proc import on_mindeye_combo_select
from 角色.style_proc import on_percentage_combo_select

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
    # lv_combo.setStyleSheet("""
    #     QComboBox {
    #         padding: 6px 10px;
    #         border: 1px solid rgba(160, 160, 160, 180);
    #         border-radius: 6px;
    #         background-color: rgba(245, 245, 245, 230);
    #         color: #333333;
    #         min-width: 110px;
    #         max-width: 140px;
    #     }
    #     QComboBox:hover {
    #         border: 1px solid #0078d7;
    #         background-color: rgba(255, 255, 255, 240);
    #     }
    #     QComboBox::drop-down {
    #         border: none;
    #         width: 28px;
    #     }
    #     QComboBox::down-arrow {
    #         image: none;
    #         width: 0;
    #         height: 0;
    #         border-left: 5px solid transparent;
    #         border-right: 5px solid transparent;
    #         border-top: 6px solid #666666;
    #         margin-right: 8px;
    #     }
    #     QComboBox::down-arrow:on {
    #         border-top: none;
    #         border-bottom: 6px solid #666666;
    #     }
    #     QComboBox QAbstractItemView {
    #         border: 1px solid rgba(140, 140, 140, 200);
    #         background-color: rgba(255, 255, 255, 245);
    #         color: #333333;
    #         selection-background-color: #0078d7;
    #         selection-color: #ffffff;
    #         outline: none;
    #     }
    #     QComboBox QAbstractItemView::item {
    #         padding: 6px 12px;
    #         min-height: 22px;
    #     }
    #     QComboBox QAbstractItemView::item:hover {
    #         background-color: rgba(0, 120, 215, 0.18);
    #         color: #333333;
    #     }
    #     QComboBox QAbstractItemView::item:selected {
    #         background-color: #0078d7;
    #         color: #ffffff;
    #     }
    #     /* 下拉列表滚动条 */
    #     QComboBox QAbstractItemView QScrollBar:vertical {
    #         background: rgba(240, 240, 240, 200);
    #         width: 8px;
    #         border-radius: 4px;
    #     }
    #     QComboBox QAbstractItemView QScrollBar::handle:vertical {
    #         background: rgba(180, 180, 180, 220);
    #         min-height: 24px;
    #         border-radius: 4px;
    #     }
    #     QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
    #         background: rgba(150, 150, 150, 240);
    #     }
    #     QComboBox QAbstractItemView QScrollBar::add-line:vertical,
    #     QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
    #         height: 0px;
    #     }
    #     QComboBox QAbstractItemView QScrollBar::add-page:vertical,
    #     QComboBox QAbstractItemView QScrollBar::sub-page:vertical {
    #         background: none;
    #     }
    # """)

    lv_combo.setStyleSheet("""
        /* ===== 主控件 ===== */
        QComboBox {
            padding: 7px 12px;
            padding-right: 28px;          /* 给箭头留空间 */
            border: 1px solid rgba(160, 160, 160, 160);
            border-radius: 8px;
            background-color: rgba(250, 250, 250, 240);
            color: #2d2d2d;
            font-size: 15px;
            min-width: 110px;
            max-width: 140px;
            selection-background-color: transparent;   /* 禁止编辑态高亮干扰 */
            selection-color: #2d2d2d;
        }
        QComboBox:hover {
            border: 1px solid #0078d7;
            background-color: #ffffff;
        }
        QComboBox:focus {
            border: 1px solid #0078d7;
            outline: none;
        }
        QComboBox:disabled {
            background-color: rgba(230, 230, 230, 200);
            color: #999999;
            border: 1px solid rgba(180, 180, 180, 150);
        }

        /* ===== 下拉按钮区域 ===== */
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 26px;
            border: none;
            border-left: 1px solid rgba(180, 180, 180, 120);
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            background: transparent;
        }
        QComboBox::drop-down:hover {
            background-color: rgba(0, 120, 215, 0.08);
        }

        /* ===== 箭头图标 ===== */
        QComboBox::down-arrow {
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #555555;
            margin-right: 2px;
        }
        QComboBox::down-arrow:on {
            border-top: none;
            border-bottom: 6px solid #0078d7;
        }
        QComboBox::down-arrow:hover {
            border-top-color: #0078d7;
        }

        /* ===== 下拉列表面板 ===== */
        QComboBox QAbstractItemView {
            border: 1px solid rgba(140, 140, 140, 180);
            border-radius: 6px;
            background-color: rgba(255, 255, 255, 252);
            color: #2d2d2d;
            selection-background-color: #0078d7;
            selection-color: #ffffff;
            outline: none;
            padding: 4px 0;               /* 列表上下内边距 */
            margin-top: 2px;              /* 面板与主控件微间距 */
        }
        QComboBox QAbstractItemView::item {
            padding: 7px 14px;
            min-height: 24px;
            border-radius: 4px;
            margin: 1px 4px;             /* 每项左右留出圆角空间 */
        }
        QComboBox::item:hover,
        QComboBox QAbstractItemView::item:hover {
            background-color: rgba(0, 120, 215, 0.35);
            color: #000000;
        }
        QComboBox::item:selected,
        QComboBox QAbstractItemView::item:selected {
            background-color: #0078d7;
            color: #ffffff;
        }
        /* 首尾项圆角修正 */
        QComboBox QAbstractItemView::item:first {
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QComboBox QAbstractItemView::item:last {
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        }

        /* ===== 滚动条 ===== */
        QComboBox QAbstractItemView QScrollBar:vertical {
            background: transparent;
            width: 6px;
            margin: 4px 1px;
            border-radius: 3px;
        }
        QComboBox QAbstractItemView QScrollBar::handle:vertical {
            background: rgba(170, 170, 170, 200);
            min-height: 28px;
            border-radius: 3px;
        }
        QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
            background: rgba(130, 130, 130, 230);
        }
        QComboBox QAbstractItemView QScrollBar::add-line:vertical,
        QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
            height: 0;
        }
        QComboBox QAbstractItemView QScrollBar::add-page:vertical,
        QComboBox QAbstractItemView QScrollBar::sub-page:vertical {
            background: none;
        }
    """)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(lv_combo, 0, 0)

    view = lv_combo.view()
    if view is not None:
        view.setMouseTracking(True)
        view.setMinimumWidth(120)
        view.setMaximumWidth(180)
        view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    lv_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
    lv_combo.setMinimumContentsLength(10)
    lv_combo.setMaxVisibleItems(10)

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
