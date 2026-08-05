
import os
import types

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMenu, QSizePolicy
from PyQt5.QtCore import Qt

from canvas_events_qt import VideoPlayerWithScrollbar
from window_qt import set_window_expand, set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top, PreviewWindow
from scrollbar_frame_qt import ScrollbarFrameWin
from tools import replace_file_extension

from 角色.style_career_win_qt import creat_career_frame
from 角色.style_active_skill_win_qt import creat_active_skill_frame
from 角色.style_passive_skill_win_qt import creat_passive_skill_frame
from 角色.style_growth_ability_win_qt import creat_growth_ability_frame
from 角色.style_growth_status_win_qt import creat_growth_status_frame
from 角色.style_resonance_win_qt import creat_resonance_frame

import 持有物.强化素材.strengthen_materials
import 战斗系统.职业.careers_info
import 战斗系统.属性.attributes_info
import 战斗系统.状态.status_info


def load_resources():
    持有物.强化素材.strengthen_materials.load_resources()
    战斗系统.职业.careers_info.get_all_career_obj()
    战斗系统.状态.status_info.get_all_statu_obj()
    战斗系统.属性.attributes_info.get_all_attribute_obj()


def show_style(scrollbar_frame_obj, style):
    scrollbar_frame_obj.destroy_components()

    parent_frame = scrollbar_frame_obj.scrollable_frame
    parent_layout = parent_frame.layout()
    if parent_layout is None:
        parent_layout = QVBoxLayout(parent_frame)
        parent_layout.setSpacing(10)
        parent_layout.setContentsMargins(10, 10, 10, 10)
        parent_layout.setAlignment(Qt.AlignTop)

    # 技能信息背景容器（背景图由 ScrollbarFrameWin 在视口层固定绘制，不随内容滚动/缩放）
    skill_bg_frame = QWidget(parent_frame)
    skill_bg_layout = QVBoxLayout(skill_bg_frame)
    skill_bg_layout.setSpacing(10)
    skill_bg_layout.setContentsMargins(10, 10, 10, 10)
    skill_bg_layout.setAlignment(Qt.AlignTop)
    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(skill_bg_frame, 0, 0, 1, 1)
        parent_layout.setRowStretch(0, 1)
        parent_layout.setColumnStretch(0, 1)
        skill_bg_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 职业
    creat_career_frame(skill_bg_frame, 0, style)

    # 主动技能
    creat_active_skill_frame(scrollbar_frame_obj, skill_bg_frame, 1, style)

    # 被动技能
    creat_passive_skill_frame(skill_bg_frame, 2, style)

    # 宝珠强化
    if style.growth_ability:
        creat_growth_ability_frame(skill_bg_frame, 3, style)
        growth_status_frame_row = 4
    else:
        growth_status_frame_row = 3

    # 成长状态
    creat_growth_status_frame(skill_bg_frame, growth_status_frame_row, style)

    # 共鸣天赋
    if style.resonance:
        creat_resonance_frame(skill_bg_frame, growth_status_frame_row + 1, style)

    scrollbar_frame_obj.update_canvas()


def get_style_win_name(style) -> str:
    if style.nicknames:
        style_win_name = style.name + f"（{style.nicknames[0]}）"
    else:
        style_win_name = style.name
    style_win_name += "-" + style.rarity
    return style_win_name


def _on_close(frame, win_name):
    win_close_manage(frame, __name__)


def creat_style_skill_win(event, parent_frame, team, style):
    load_resources()

    open_style_win = get_style_win_name(style)
    if is_win_open(open_style_win, __name__):
        win_set_top(open_style_win, __name__)
        return "break"

    style_win_frame = creat_Toplevel(open_style_win, 812, 880, 650, 70)
    set_window_icon(style_win_frame, team.logo_path)
    set_window_expand(style_win_frame, rowspan=1, columnspan=2)
    artwork_path = style.path.replace("_Thumbnail", "")
    bg_image_path = artwork_path if os.path.exists(artwork_path) else None
    scrollbar_frame_obj = ScrollbarFrameWin(style_win_frame, columnspan=2, bg_image_path=bg_image_path, bg_opacity="70%")

    win_open_manage(style_win_frame, __name__)

    def on_close(self, event):
        win_close_manage(style_win_frame, __name__)
        event.accept()

    style_win_frame.closeEvent = types.MethodType(on_close, style_win_frame)

    # 禁用界面更新，批量创建完成后再一次性刷新，减少窗口卡顿
    style_win_frame.setUpdatesEnabled(False)
    try:
        show_style(scrollbar_frame_obj, style)
    finally:
        style_win_frame.setUpdatesEnabled(True)
        style_win_frame.update()

    return "break"


def creat_style_right_menu(event, parent_frame, team, style):
    right_click_menu = QMenu(parent_frame)
    right_click_menu.addAction("动画", lambda: show_style_animation(parent_frame, team, style))
    right_click_menu.addAction("立绘", lambda: show_style_artwork(parent_frame, team, style))
    right_click_menu.addAction("3D立绘", lambda: show_style_artwork_3d(parent_frame, team, style))
    right_click_menu.exec_(event.globalPos())


def _on_animation_close(frame, win_name, player):
    win_close_manage(frame, __name__, player)


def show_style_animation(parent_frame, team, style):
    animation_path = style.path.replace("_Thumbnail", "")
    animation_path = replace_file_extension(animation_path, "webm")

    if not os.path.exists(animation_path):
        return

    open_style_win = get_style_win_name(style) + "-animation"
    if is_win_open(open_style_win, __name__):
        win_set_top(open_style_win, __name__)
        return "break"

    style_animation_win_frame = creat_Toplevel(open_style_win, 1362, 767, x=300, y=120)
    set_window_icon(style_animation_win_frame, team.logo_path)
    win_open_manage(style_animation_win_frame, __name__)

    player = VideoPlayerWithScrollbar(style_animation_win_frame, 1362, 767, animation_path)

    def on_close(self, event):
        win_close_manage(style_animation_win_frame, __name__, player)
        event.accept()

    style_animation_win_frame.closeEvent = types.MethodType(on_close, style_animation_win_frame)


_qt_open_windows = {}
_qt_app = None


def show_style_artwork(parent_frame, team, style):
    artwork_path = style.path.replace("_Thumbnail", "")
    if not os.path.exists(artwork_path):
        return

    open_style_win = get_style_win_name(style) + "-artwork"

    if open_style_win in _qt_open_windows:
        win = _qt_open_windows[open_style_win]
        win.showNormal()
        win.raise_()
        win.activateWindow()
        return "break"

    global _qt_app
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        _qt_app = app
    else:
        _qt_app = app

    preview_win = PreviewWindow(title_name=open_style_win)
    preview_win.setAttribute(Qt.WA_DeleteOnClose, True)

    if hasattr(team, 'logo_path') and os.path.exists(team.logo_path):
        preview_win.setWindowIcon(QIcon(team.logo_path))

    preview_win.show_image(artwork_path)

    def custom_close_event(self_win, event):
        if open_style_win in _qt_open_windows:
            del _qt_open_windows[open_style_win]
        super(PreviewWindow, self_win).closeEvent(event)

    preview_win.closeEvent = types.MethodType(custom_close_event, preview_win)

    preview_win.show()
    _qt_open_windows[open_style_win] = preview_win


def _on_artwork_3d_close(frame, win_name, displayer):
    win_close_manage(frame, __name__, displayer)


def show_style_artwork_3d(parent_frame, team, style):
    artwork_3d_path = style.path.replace("_Thumbnail", "_3d")
    artwork_3d_path = replace_file_extension(artwork_3d_path, "png")

    if not os.path.exists(artwork_3d_path):
        return

    open_style_win = get_style_win_name(style) + "-artwork-3d"
    if is_win_open(open_style_win, __name__):
        win_set_top(open_style_win, __name__)
        return "break"

    style_artwork_3d_win_frame = creat_Toplevel(open_style_win, x=770, y=150)
    set_window_icon(style_artwork_3d_win_frame, team.logo_path)
    win_open_manage(style_artwork_3d_win_frame, __name__)

    from canvas_events_qt import ArtworkDisplayerHeight
    displayer = ArtworkDisplayerHeight(style_artwork_3d_win_frame, artwork_3d_path, 710, 0)

    def on_close(self, event):
        win_close_manage(style_artwork_3d_win_frame, __name__, displayer)
        event.accept()

    style_artwork_3d_win_frame.closeEvent = types.MethodType(on_close, style_artwork_3d_win_frame)

    return "break"
