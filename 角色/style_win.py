
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import ArtworkDisplayerHeight
from canvas_events import ImageViewerWithScrollbar, VideoPlayerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_win import ScrollbarFrameWin

from 角色.style_career_win import creat_career_frame
from 角色.style_active_skill_win import creat_active_skill_frame
from 角色.style_passive_skill_win import creat_passive_skill_frame
from 角色.style_growth_ability_win import creat_growth_ability_frame
from 角色.style_growth_status_win import creat_growth_status_frame
from 角色.style_resonance_win import creat_resonance_frame

import 持有物.强化素材.strengthen_materials
import 战斗系统.职业.careers_info
import 战斗系统.属性.attributes_info
import 战斗系统.状态.status_info

# 加载资源文件
def load_resources():
    持有物.强化素材.strengthen_materials.load_resources()
    战斗系统.职业.careers_info.get_all_career_obj()
    战斗系统.状态.status_info.get_all_statu_obj()
    战斗系统.属性.attributes_info.get_all_attribute_obj()

def show_style(scrollbar_frame_obj, style):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    parent_frame = scrollbar_frame_obj.scrollable_frame

    # 职业
    creat_career_frame(parent_frame, 0, style)

    # 主动技能
    creat_active_skill_frame(scrollbar_frame_obj, parent_frame, 1, style)

    # 被动技能
    creat_passive_skill_frame(parent_frame, 2, style)

    # 宝珠强化
    if style.growth_ability:
        creat_growth_ability_frame(parent_frame, 3, style)
        growth_status_frame_row = 4
    else:
        growth_status_frame_row = 3

    # 成长状态
    creat_growth_status_frame(parent_frame, growth_status_frame_row, style)

    # 共鸣天赋
    if style.resonance:
        creat_resonance_frame(parent_frame, growth_status_frame_row+1, style)

    scrollbar_frame_obj.update_canvas()

# 获取别名
def get_style_win_name(style) -> str:  
    if style.nicknames:
        style_win_name = style.name + f"（{style.nicknames[0]}）"
    else:
        style_win_name = style.name
    style_win_name += "-" + style.rarity

    return style_win_name

def creat_style_skill_win(event, parent_frame, team, style):

    # 初始化资源文件
    load_resources()

    open_style_win = get_style_win_name(style)
    # 重复打开时，窗口置顶并直接返回
    if is_win_open(open_style_win, __name__):
        win_set_top(open_style_win, __name__)
        return "break"

    style_win_frame = creat_Toplevel(open_style_win, 812, 880, 650, 70) #780
    set_window_icon(style_win_frame, team.logo_path)
    set_window_expand(style_win_frame, rowspan=1, columnspan=2)
    scrollbar_frame_obj = ScrollbarFrameWin(style_win_frame, columnspan=2)

    win_open_manage(style_win_frame, __name__)

    # 绑定鼠标点击事件到父窗口，点击置顶
    style_win_frame.bind("<Button-1>", 
        lambda event: win_set_top(open_style_win, __name__))
    # 窗口关闭时清理
    style_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(style_win_frame, __name__))


    show_style(scrollbar_frame_obj, style)

    return "break"  # 阻止事件冒泡

# 创建右键菜单
def creat_style_right_menu(event, parent_frame, team, style):
    
    right_click_menu = ttk.Menu(parent_frame, tearoff=0)

    right_click_menu.add_command(label="动画", 
        command=lambda: show_style_animation(parent_frame, team, style))

    right_click_menu.add_command(label="立绘", 
        command=lambda: show_style_artwork(parent_frame, team, style))

    right_click_menu.add_command(label="3D立绘", 
        command=lambda: show_style_artwork_3d(parent_frame, team, style))

    right_click_menu.post(event.x_root, event.y_root)


# 显示风格动画
def show_style_animation(parent_frame, team, style):

    animation_path = style.path.replace("_Thumbnail", "")
    animation_path = animation_path[:-4] + "webm"

    # 判断有没有动画
    if os.path.exists(animation_path):

        open_style_win = get_style_win_name(style) + "-animation"
        # 重复打开时，窗口置顶并直接返回
        if is_win_open(open_style_win, __name__):
            win_set_top(open_style_win, __name__)
            return "break"

        style_animation_win_frame = creat_Toplevel(open_style_win, 1366, 768, x=300, y=120)
        set_window_icon(style_animation_win_frame, team.logo_path)
        win_open_manage(style_animation_win_frame, __name__)

        player = VideoPlayerWithScrollbar(style_animation_win_frame, 1366, 768, animation_path)

        # 窗口关闭时清理
        style_animation_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (win_close_manage(style_animation_win_frame, __name__, player)))
    else:
        return

# 显示风格静态图
def show_style_artwork(parent_frame, team, style):

    artwork_path = style.path.replace("_Thumbnail", "")

    if os.path.exists(artwork_path):
        open_style_win = get_style_win_name(style) + "-artwork"
        # 重复打开时，窗口置顶并直接返回
        if is_win_open(open_style_win, __name__):
            win_set_top(open_style_win, __name__)
            return "break"

        style_artwork_win_frame = creat_Toplevel(open_style_win, 1366, 769, x=300, y=120)
        set_window_icon(style_artwork_win_frame, team.logo_path)
        win_open_manage(style_artwork_win_frame, __name__)

        displayer = ImageViewerWithScrollbar(style_artwork_win_frame, 1366, 769, artwork_path)

        # 窗口关闭时清理
        style_artwork_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (win_close_manage(style_artwork_win_frame, __name__, displayer)))

    else:
        return


# 显示风格3d静态图
def show_style_artwork_3d(parent_frame, team, style):

    artwork_3d_path = style.path.replace("_Thumbnail", "_3d")
    artwork_3d_path = artwork_3d_path[:-4] + "png"

    if os.path.exists(artwork_3d_path):

        open_style_win = get_style_win_name(style) + "-artwork-3d"
        # 重复打开时，窗口置顶并直接返回
        if is_win_open(open_style_win, __name__):
            win_set_top(open_style_win, __name__)
            return "break"

        style_artwork_3d_win_frame = creat_Toplevel(open_style_win, x=770, y=150)
        set_window_icon(style_artwork_3d_win_frame, team.logo_path)
        win_open_manage(style_artwork_3d_win_frame, __name__)

        displayer = ArtworkDisplayerHeight(style_artwork_3d_win_frame, artwork_3d_path, 710, 0)
        
        # 窗口关闭时清理
        style_artwork_3d_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (win_close_manage(style_artwork_3d_win_frame, __name__, displayer)))

    else:
        return


