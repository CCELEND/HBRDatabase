
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout
from PyQt5.QtCore import Qt

from canvas_events_qt import get_pixmap, create_canvas_with_image
from window_qt import set_window_expand, creat_Toplevel, set_window_icon_webp
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 角色.style_text import output_skill_effect
import 战斗系统.状态.status_info


def load_resources():
    战斗系统.状态.status_info.get_all_statu_obj()


def creat_desc_frame(row_frame, orb_skill):
    desc_frame = QFrame(row_frame)
    desc_frame.setLayout(QGridLayout())
    desc_frame.layout().setContentsMargins(5, 0, 5, 5)
    desc_frame.layout().setSpacing(0)
    desc_frame.layout().setColumnStretch(0, 4)
    desc_frame.layout().setColumnStretch(1, 1)

    desc_lab = QLabel(orb_skill.description)
    desc_lab.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    desc_lab.setWordWrap(True)
    desc_lab.setStyleSheet("font-family: Monospace; font-size: 10px; font-weight: bold;")
    desc_frame.layout().addWidget(desc_lab, 0, 0)

    if orb_skill.max_uses:
        text = "SP" + orb_skill.sp_cost + '\n' + orb_skill.max_uses
    else:
        text = "SP" + orb_skill.sp_cost + '\n' + "∞"
    sp_use_lab = QLabel(text)
    sp_use_lab.setAlignment(Qt.AlignRight | Qt.AlignTop)
    sp_use_lab.setStyleSheet("font-family: Monospace; font-size: 10px; font-weight: bold;")
    desc_frame.layout().addWidget(sp_use_lab, 0, 1)

    row_frame.layout().addWidget(desc_frame)


def creat_orb_skill_frame(scrollbar_frame_obj, orb_skill):
    scrollbar_frame_obj.destroy_components()

    row_frame = QFrame(scrollbar_frame_obj.scrollable_frame)
    row_frame.setFrameShape(QFrame.StyledPanel)
    row_frame.setLayout(QVBoxLayout())
    row_frame.layout().setContentsMargins(10, 10, 10, 10)
    row_frame.layout().setSpacing(5)

    title_label = QLabel(orb_skill.name)
    title_label.setStyleSheet("font-weight: bold;")
    row_frame.layout().addWidget(title_label)

    creat_desc_frame(row_frame, orb_skill)

    for j, skill in enumerate(orb_skill.effects):
        effect_frame = QFrame(row_frame)
        effect_frame.setLayout(QGridLayout())
        effect_frame.layout().setContentsMargins(0, 0, 0, 5)
        effect_frame.layout().setSpacing(0)
        effect_frame.layout().setColumnStretch(0, 1)
        effect_frame.layout().setColumnStretch(1, 6)

        effect_pixmap = get_pixmap(
            战斗系统.状态.status_info.status[skill.effect_type].path, (60, 60)
        )
        effect_canvas = create_canvas_with_image(
            effect_frame, effect_pixmap, 60, 60, 0, 0, 0, 0
        )

        text = output_skill_effect(
            skill.turn_num, skill.duration, skill.target, skill.effect_type,
            战斗系统.状态.status_info.status[skill.effect_type].description,
            skill.value, skill.attribute_multiplier,
            skill.attribute_difference,
            IsActive=True
        )

        desc_lab = QLabel(text)
        desc_lab.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        desc_lab.setWordWrap(True)
        desc_lab.setStyleSheet("font-family: Monospace; font-size: 10px; font-weight: bold;")
        effect_frame.layout().addWidget(desc_lab, 0, 1)

        row_frame.layout().addWidget(effect_frame)

    scrollbar_frame_obj.scrollable_frame.layout().addWidget(row_frame)
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

    orb_win_frame.mousePressEvent = lambda ev: win_set_top(orb_win_frame, __name__)
    orb_win_frame.closeEvent = lambda ev: win_close_manage(orb_win_frame, __name__)

    creat_orb_skill_frame(scrollbar_frame_obj, orb_skill)

    return "break"
