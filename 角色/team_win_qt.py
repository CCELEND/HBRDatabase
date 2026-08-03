
import os
import types

from PyQt5.QtWidgets import QWidget, QLabel, QGroupBox, QGridLayout, QMenu
from PyQt5.QtCore import Qt
from canvas_events_qt import bind_canvas_events, get_pixmap, create_image_label, WrappedLabel
from canvas_events_qt import mouse_bind_canvas_events2, right_click_bind_canvas_events, set_tooltip
from canvas_events_qt import ArtworkDisplayerHeight
from window_qt import set_window_expand, set_window_icon, creat_Toplevel, MONO_FONT
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_qt import ScrollbarFrameWin

from 角色.team_info import get_team_obj, get_all_team_obj, Team, Role
from 角色.role_info import get_role_master_img
from 角色.style_win_qt import creat_style_skill_win, creat_style_right_menu
from 角色.master_skill_win_qt import creat_master_skill_win

import 战斗系统.武器.weapons_info

def load_resources():
    战斗系统.武器.weapons_info.get_all_weapon_obj()

def creat_role_right_menu(event, parent_frame, role: Role, team: Team):
    right_click_menu = QMenu(parent_frame)
    right_click_menu.addAction("全身画", lambda: show_role_full_img(event, parent_frame, role, team))
    right_click_menu.exec_(event.globalPos())

def show_role_full_img(event, parent_frame, role: Role, team: Team):
    open_role_win = role.name + "-full"
    if is_win_open(open_role_win, __name__):
        win_set_top(open_role_win, __name__)
        return "break"

    role_full_img_frame = creat_Toplevel(open_role_win, x=770, y=100)
    set_window_icon(role_full_img_frame, team.logo_path)
    win_open_manage(role_full_img_frame, __name__)

    role_full_path = role.img_path.replace("Profile", "")
    displayer = ArtworkDisplayerHeight(role_full_img_frame, role_full_path, 840, padding=70)

    def on_close(self, event):
        win_close_manage(role_full_img_frame, __name__, displayer)
        event.accept()

    role_full_img_frame.closeEvent = types.MethodType(on_close, role_full_img_frame)

    return "break"

def show_role_img(event, parent_frame, role: Role, team: Team):
    open_role_win = role.name
    if is_win_open(open_role_win, __name__):
        win_set_top(open_role_win, __name__)
        return "break"

    role_img_frame = creat_Toplevel(open_role_win, 444, 508, 600, 200)
    set_window_icon(role_img_frame, team.logo_path)
    win_open_manage(role_img_frame, __name__)

    displayer = ArtworkDisplayerHeight(role_img_frame, role.img_path, 508)

    return "break"

def bind_style_canvas(parent_frame, team: Team, style, x, y):
    outer_frame = QWidget(parent_frame)
    outer_frame.setFixedSize(140, 134)

    outer_layout = QGridLayout(outer_frame)
    outer_layout.setSpacing(0)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    pixmap = get_pixmap(style.path, (90, 90))
    canvas = create_image_label(outer_frame, pixmap, 130, 130)
    set_tooltip(canvas, style.name)
    mouse_bind_canvas_events2(canvas)

    bind_canvas_events(canvas,
        creat_style_skill_win, parent_frame=parent_frame, team=team, style=style)
    right_click_bind_canvas_events(canvas,
        creat_style_right_menu, parent_frame=parent_frame, team=team, style=style)

    outer_layout.addWidget(canvas, 0, 0, alignment=Qt.AlignCenter)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(outer_frame, x, y, alignment=Qt.AlignCenter)

    return outer_frame

def bind_master_skill_canvas(parent_frame, role: Role, x, y):
    photo_path = get_role_master_img(role)

    outer_frame = QWidget(parent_frame)
    outer_frame.setFixedSize(140, 134)

    outer_layout = QGridLayout(outer_frame)
    outer_layout.setSpacing(0)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    pixmap = get_pixmap(photo_path, (90, 90))
    canvas = create_image_label(outer_frame, pixmap, 130, 130)
    set_tooltip(canvas, role.name)
    mouse_bind_canvas_events2(canvas)

    bind_canvas_events(canvas,
        creat_master_skill_win, parent_frame=outer_frame, role=role)

    outer_layout.addWidget(canvas, 0, 0, alignment=Qt.AlignCenter)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(outer_frame, x, y, alignment=Qt.AlignCenter)

    return outer_frame

def show_rarity(frame, role: Role, team: Team, row=2):
    frame_layout = frame.layout()
    if frame_layout is None:
        return row

    if role.master_skill:
        MasterSkillframe = QWidget(frame)
        MasterSkillframe.setFixedHeight(145)
        frame_layout.addWidget(MasterSkillframe, row, 0, 1, 1)

        master_layout = QGridLayout(MasterSkillframe)
        master_layout.setSpacing(5)
        master_layout.setContentsMargins(10, 5, 10, 5)

        pixmap = get_pixmap("./角色/iconMasterSkill.png", (120, 120))
        canvasMasterSkill = create_image_label(MasterSkillframe, pixmap, 134, 134)
        mouse_bind_canvas_events2(canvasMasterSkill)
        bind_canvas_events(canvasMasterSkill,
            creat_master_skill_win, parent_frame=MasterSkillframe, role=role)
        master_layout.addWidget(canvasMasterSkill, 0, 0, alignment=Qt.AlignCenter)
        master_layout.setColumnStretch(1, 1)

        row += 1

    if role.Astyles:
        RarityAframe = QWidget(frame)
        frame_layout.addWidget(RarityAframe, row, 0, 1, 1)
        rarity_layout = QGridLayout(RarityAframe)
        rarity_layout.setSpacing(5)
        rarity_layout.setContentsMargins(10, 5, 10, 5)

        pixmapRarityA = get_pixmap("./角色/IconRarityA.png", (130, 130))
        canvasRarityA = create_image_label(RarityAframe, pixmapRarityA, 134, 134)
        rarity_layout.addWidget(canvasRarityA, 0, 0, alignment=Qt.AlignCenter)
        for a, Astyle in enumerate(role.Astyles):
            bind_style_canvas(RarityAframe, team, Astyle, 0, a + 1)
        rarity_layout.setColumnStretch(len(role.Astyles) + 1, 1)

        row += 1

    if role.Sstyles:
        RaritySframe = QWidget(frame)
        frame_layout.addWidget(RaritySframe, row, 0, 1, 1)
        rarity_layout = QGridLayout(RaritySframe)
        rarity_layout.setSpacing(5)
        rarity_layout.setContentsMargins(10, 5, 10, 5)

        pixmapRarityS = get_pixmap("./角色/IconRarityS.png", (130, 130))
        canvasRarityS = create_image_label(RaritySframe, pixmapRarityS, 134, 134)
        rarity_layout.addWidget(canvasRarityS, 0, 0, alignment=Qt.AlignCenter)
        for s, Sstyle in enumerate(role.Sstyles):
            bind_style_canvas(RaritySframe, team, Sstyle, 0, s + 1)
        rarity_layout.setColumnStretch(len(role.Sstyles) + 1, 1)

        row += 1

    if role.SSstyles:
        RaritySSframe = QWidget(frame)
        frame_layout.addWidget(RaritySSframe, row, 0, 1, 1)
        rarity_layout = QGridLayout(RaritySSframe)
        rarity_layout.setSpacing(5)
        rarity_layout.setContentsMargins(10, 5, 10, 5)

        pixmapRaritySS = get_pixmap("./角色/IconRaritySS.png", (130, 130))
        canvasRaritySS = create_image_label(RaritySSframe, pixmapRaritySS, 134, 134)
        rarity_layout.addWidget(canvasRaritySS, 0, 0, alignment=Qt.AlignCenter)
        for ss, SSstyle in enumerate(role.SSstyles):
            bind_style_canvas(RaritySSframe, team, SSstyle, 0, ss + 1)
        rarity_layout.setColumnStretch(len(role.SSstyles) + 1, 1)

        row += 1

    if role.SSRstyles:
        RaritySSRframe = QWidget(frame)
        frame_layout.addWidget(RaritySSRframe, row, 0, 1, 1)
        rarity_layout = QGridLayout(RaritySSRframe)
        rarity_layout.setSpacing(5)
        rarity_layout.setContentsMargins(10, 5, 10, 5)

        pixmapRaritySSR = get_pixmap("./角色/IconRaritySSR.png", (130, 130))
        canvasRaritySSR = create_image_label(RaritySSRframe, pixmapRaritySSR, 134, 134)
        rarity_layout.addWidget(canvasRaritySSR, 0, 0, alignment=Qt.AlignCenter)
        for ssr, SSRstyle in enumerate(role.SSRstyles):
            bind_style_canvas(RaritySSRframe, team, SSRstyle, 0, ssr + 1)
        rarity_layout.setColumnStretch(len(role.SSRstyles) + 1, 1)

    return row

def creat_team_desc_frame(parent_frame, team: Team):
    team_desc_frame = QGroupBox(team.name)
    team_desc_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(team_desc_frame, 0, 0, 1, 4)

    desc_layout = QGridLayout(team_desc_frame)
    desc_layout.setSpacing(5)
    desc_layout.setContentsMargins(10, 10, 10, 10)
    desc_layout.setColumnStretch(0, 1)
    desc_layout.setColumnStretch(1, 9)

    team_desc_pixmap = get_pixmap(team.logo_path, (64, 64))
    team_desc_label = create_image_label(team_desc_frame, team_desc_pixmap, 100, 64)
    desc_layout.addWidget(team_desc_label, 0, 0, alignment=Qt.AlignCenter)

    team_desc_text = WrappedLabel(team.description)
    # team_desc_text = QLabel(team.description)
    team_desc_text.setFont(MONO_FONT)
    team_desc_text.setWordWrap(True)
    team_desc_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    desc_layout.addWidget(team_desc_text, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    return team_desc_frame

def creat_weapon_frame(parent_frame, role: Role):
    weapon = 战斗系统.武器.weapons_info.weapons[role.weapon]

    weapon_frame = QWidget(parent_frame)
    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(weapon_frame, 0, 2, 1, 1)

    weapon_layout = QGridLayout(weapon_frame)
    weapon_layout.setSpacing(5)
    weapon_layout.setContentsMargins(5, 5, 5, 5)

    weapon_pixmap = get_pixmap(weapon.path, (60, 60))
    weapon_label = create_image_label(weapon_frame, weapon_pixmap, 100, 200)
    weapon_layout.addWidget(weapon_label, 0, 0, alignment=Qt.AlignCenter)

    return weapon_frame

def _ensure_grid_layout(widget):
    layout = widget.layout()
    if isinstance(layout, QGridLayout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            l = item.layout()
            if l is not None:
                l.deleteLater()
        return layout
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            l = item.layout()
            if l is not None:
                l.deleteLater()
        layout.deleteLater()
    new_layout = QGridLayout(widget)
    return new_layout

def show_team(scrollbar_frame_obj, team: Team):
    scrollbar_frame_obj.destroy_components()

    scrollable_frame = scrollbar_frame_obj.scrollable_frame
    grid_container = QWidget(scrollable_frame)
    scroll_layout = QGridLayout(grid_container)
    scroll_layout.setSpacing(10)
    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setAlignment(Qt.AlignTop)
    for col in range(4):
        scroll_layout.setColumnStretch(col, 1)

    scrollbar_frame_obj.layout.addWidget(grid_container)

    creat_team_desc_frame(grid_container, team)

    for i, role in enumerate(team.roles):
        frame = QGroupBox(role.name)
        frame.setFont(MONO_FONT)
        scroll_layout.addWidget(frame, i + 1, 0, 1, 4)

        frame_layout = QGridLayout(frame)
        frame_layout.setSpacing(5)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setRowStretch(0, 1)
        frame_layout.setRowStretch(1, 1)
        frame_layout.setColumnStretch(0, 1)

        desc_frame = QWidget(frame)
        frame_layout.addWidget(desc_frame, 0, 0, 1, 4)
        desc_layout = QGridLayout(desc_frame)
        desc_layout.setSpacing(5)
        desc_layout.setContentsMargins(0, 10, 0, 10)
        desc_layout.setColumnStretch(0, 1)
        desc_layout.setColumnStretch(1, 4)
        desc_layout.setColumnStretch(2, 1)

        pixmap = get_pixmap(role.img_path, (130, 254))
        canvas = create_image_label(desc_frame, pixmap, 200, 254)
        mouse_bind_canvas_events2(canvas)
        bind_canvas_events(canvas,
            show_role_full_img, parent_frame=frame, role=role, team=team)
        desc_layout.addWidget(canvas, 0, 0, 2, 1, alignment=Qt.AlignCenter)

        label = QLabel(role.description)
        label.setFont(MONO_FONT)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        desc_layout.addWidget(label, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        creat_weapon_frame(desc_frame, role)

        show_rarity(frame, role, team)

    scrollbar_frame_obj.update_canvas()

def creat_team_win(parent_frame, team_name):
    if is_win_open(team_name, __name__):
        win_set_top(team_name, __name__)
        return

    get_all_team_obj()
    team = get_team_obj(team_name)

    load_resources()

    team_win_frame = creat_Toplevel(team_name, 1130, 880, 90, 80)
    set_window_icon(team_win_frame, team.logo_path)
    set_window_expand(team_win_frame, rowspan=1, columnspan=2)
    scrollbar_frame_obj = ScrollbarFrameWin(team_win_frame, columnspan=2)
    win_open_manage(team_win_frame, __name__)

    def on_close(self, event):
        win_close_manage(team_win_frame, __name__)
        event.accept()

    team_win_frame.closeEvent = types.MethodType(on_close, team_win_frame)

    show_team(scrollbar_frame_obj, team)

    return "break"
