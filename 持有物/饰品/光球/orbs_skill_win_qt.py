import types

from PyQt5.QtWidgets import QGroupBox, QWidget, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from canvas_events_qt import get_pixmap, create_image_label, WrappedLabel
from window_qt import set_window_expand, creat_Toplevel, set_window_icon_webp, MONO_FONT
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 角色.style_text import output_skill_effect
import 战斗系统.状态.status_info

def load_resources():
    战斗系统.状态.status_info.get_all_statu_obj()

def creat_orb_skill_frame(scrollbar_frame_obj, orb_skill):
    scrollbar_frame_obj.destroy_components()

    parent_frame = scrollbar_frame_obj.scrollable_frame
    parent_layout = parent_frame.layout()
    if parent_layout is None:
        parent_layout = QGridLayout(parent_frame)

    parent_layout.setSpacing(10)
    parent_layout.setContentsMargins(10, 10, 10, 10)
    parent_layout.setAlignment(Qt.AlignTop)
    parent_layout.setColumnStretch(0, 1)

    # 使用 QGroupBox 替代 QFrame，标题自动集成到分组框中
    row_frame = QGroupBox(orb_skill.name)
    row_frame.setFont(MONO_FONT)
    parent_layout.addWidget(row_frame, 0, 0)

    row_layout = QGridLayout(row_frame)
    row_layout.setSpacing(5)
    row_layout.setContentsMargins(10, 10, 10, 10)
    row_layout.setColumnStretch(0, 4)  # 描述列
    row_layout.setColumnStretch(1, 1)  # SP列

    # --- 描述与SP区域 ---
    desc_lab = WrappedLabel(orb_skill.description)
    desc_lab.setFont(MONO_FONT)
    desc_lab.setWordWrap(True)
    desc_lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    row_layout.addWidget(desc_lab, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    sp_text = f"SP{orb_skill.sp_cost}\n{orb_skill.max_uses}" if orb_skill.max_uses else f"SP{orb_skill.sp_cost}\n∞"
    sp_lab = QLabel(sp_text)
    sp_lab.setFont(MONO_FONT)
    sp_lab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    row_layout.addWidget(sp_lab, 0, 1, alignment=Qt.AlignRight | Qt.AlignVCenter)

    # --- 效果列表 ---
    current_row = 1
    for skill in orb_skill.effects:
        effect_frame = QWidget()
        effect_layout = QGridLayout(effect_frame)
        effect_layout.setSpacing(5)
        effect_layout.setContentsMargins(0, 0, 0, 5)
        effect_layout.setColumnStretch(0, 1)
        effect_layout.setColumnStretch(1, 6)

        effect_path = 战斗系统.状态.status_info.status[skill.effect_type].path
        effect_pixmap = get_pixmap(effect_path, (60, 60))
        effect_label = create_image_label(effect_frame, effect_pixmap, 60, 60)
        effect_layout.addWidget(effect_label, 0, 0, alignment=Qt.AlignCenter)

        text = output_skill_effect(
            skill.turn_num, skill.duration, skill.target, skill.effect_type,
            战斗系统.状态.status_info.status[skill.effect_type].description,
            skill.value, skill.attribute_multiplier,
            skill.attribute_difference,
            IsActive=True
        )

        effect_desc_lab = WrappedLabel(text)
        effect_desc_lab.setFont(MONO_FONT)
        effect_desc_lab.setWordWrap(True)
        effect_desc_lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        effect_layout.addWidget(effect_desc_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        row_layout.addWidget(effect_frame, current_row, 0, 1, 2)
        current_row += 1

    scrollbar_frame_obj.update_canvas()

def creat_orb_skill_win(event, parent_frame, orb):
    load_resources()
    orb_skill = orb.skill
    open_orb_win = orb_skill.name

    if is_win_open(open_orb_win, __name__):
        win_set_top(open_orb_win, __name__)
        return "break"

    orb_win_frame = creat_Toplevel(open_orb_win, 812, 300, 350, 280)
    set_window_expand(orb_win_frame, rowspan=1, columnspan=2)
    set_window_icon_webp(orb_win_frame, orb.path)

    scrollbar_frame_obj = ScrollbarFrameWin(orb_win_frame, columnspan=2)
    win_open_manage(orb_win_frame, __name__)

    def on_close(self, ev):
        win_close_manage(orb_win_frame, __name__)
        ev.accept()

    orb_win_frame.closeEvent = types.MethodType(on_close, orb_win_frame)

    creat_orb_skill_frame(scrollbar_frame_obj, orb_skill)
    return "break"