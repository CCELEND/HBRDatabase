
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import ImageViewerWithScrollbar, VideoPlayerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

from 角色.style_active_skill_win import creat_active_skill_frame
from 角色.style_passive_skill_win import creat_passive_skill_frame
from 角色.style_growth_ability_win import creat_growth_ability_frame
from 角色.style_growth_status_win import creat_growth_status_frame

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

# 职能 frame
def creat_career_frame(parent_frame, style):

    career = 战斗系统.职业.careers_info.careers[style.career]
    career_frame = ttk.LabelFrame(parent_frame, text=style.career)
    career_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    career_frame.grid_rowconfigure(0, weight=1)

    career_photo = get_photo(career.path, (200, 40))
    career_canvas = create_canvas_with_image(career_frame, 
        career_photo, 240, 40, 20, 0, 0, 0)

def show_style(scrollbar_frame_obj, style):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    # 职业
    creat_career_frame(scrollbar_frame_obj.scrollable_frame, style)

    # 主动技能
    creat_active_skill_frame(scrollbar_frame_obj.scrollable_frame, style)

    # 被动技能
    creat_passive_skill_frame(scrollbar_frame_obj.scrollable_frame, style)

    # 宝珠强化
    if style.growth_ability:
        creat_growth_ability_frame(scrollbar_frame_obj.scrollable_frame, style)
        growth_status_row = 4
    else:
        growth_status_row = 3

    # 成长状态
    creat_growth_status_frame(scrollbar_frame_obj.scrollable_frame, style, growth_status_row)

    scrollbar_frame_obj.update_canvas()

# 获取别名
def get_style_win_name(style):  
    if style.nicknames:
        style_win_name = style.name + f"（{style.nicknames[0]}）"
    else:
        style_win_name = style.name
    style_win_name += "-" + style.rarity

    return style_win_name


# 已打开的风格窗口字典，键：风格名，值：窗口句柄
open_style_wins = {}
# 关闭窗口时，清除风格名列表中对应的风格名，并销毁窗口
def style_win_closing(parent_frame):

    open_style_win = parent_frame.title()
    while open_style_win in open_style_wins:
        del open_style_wins[open_style_win]

    parent_frame.destroy()  # 销毁窗口

# 清除所有打开的窗口
# 遍历时不能修改字典元素，遍历条件应改为列表
def clean_up_open_style_wins():
    for open_style_win in list(open_style_wins.keys()):
        style_win_frame = open_style_wins[open_style_win]
        del open_style_wins[open_style_win]
        style_win_frame.destroy()  # 销毁窗口


def creat_style_skill_win(event, parent_frame, team, style):

    # 初始化资源文件
    load_resources()

    open_style_win = get_style_win_name(style)
    # 重复打开时，窗口置顶并直接返回
    if open_style_win in open_style_wins:
        # 判断窗口是否存在
        if open_style_wins[open_style_win].winfo_exists():
            set_window_top(open_style_wins[open_style_win])
            return "break"
        del open_style_wins[open_style_win]

    style_win_frame = creat_Toplevel(open_style_win, 812, 880, 650, 70) #780
    set_window_icon(style_win_frame, team.logo_path)
    set_window_expand(style_win_frame, rowspan=1, columnspan=2)
    scrollbar_frame_obj = ScrollbarFrameWin(style_win_frame, columnspan=2)

    open_style_wins[open_style_win] = style_win_frame

    # 绑定鼠标点击事件到父窗口，点击置顶
    style_win_frame.bind("<Button-1>", lambda event: set_window_top(style_win_frame))
    # 窗口关闭时清理
    style_win_frame.protocol("WM_DELETE_WINDOW", lambda: style_win_closing(style_win_frame))

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
        if open_style_win in open_style_wins:
            # 判断窗口是否存在
            if open_style_wins[open_style_win].winfo_exists():
                set_window_top(open_style_wins[open_style_win])
                return "break"
            del open_style_wins[open_style_win]

        style_animation_win_frame = creat_Toplevel(open_style_win, 1366, 768, x=300, y=120)
        set_window_icon(style_animation_win_frame, team.logo_path)
        open_style_wins[open_style_win] = style_animation_win_frame

        player = VideoPlayerWithScrollbar(style_animation_win_frame, 1366, 768, animation_path)

        # 窗口关闭时清理
        style_animation_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (player.destroy(), style_win_closing(style_animation_win_frame)))
    else:
        return

# 显示风格静态图
def show_style_artwork(parent_frame, team, style):

    artwork_path = style.path.replace("_Thumbnail", "")

    if os.path.exists(artwork_path):
        open_style_win = get_style_win_name(style) + "-artwork"
        # 重复打开时，窗口置顶并直接返回
        if open_style_win in open_style_wins:
            # 判断窗口是否存在
            if open_style_wins[open_style_win].winfo_exists():
                set_window_top(open_style_wins[open_style_win])
                return "break"
            del open_style_wins[open_style_win]

        style_artwork_win_frame = creat_Toplevel(open_style_win, 1366, 769, x=300, y=120)
        set_window_icon(style_artwork_win_frame, team.logo_path)
        open_style_wins[open_style_win] = style_artwork_win_frame

        displayer = ImageViewerWithScrollbar(style_artwork_win_frame, 1366, 769, artwork_path)

        # 窗口关闭时清理
        style_artwork_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (displayer.destroy(), style_win_closing(style_artwork_win_frame)))

    else:
        return


# 显示风格3d静态图
def show_style_artwork_3d(parent_frame, team, style):

    artwork_3d_path = style.path.replace("_Thumbnail", "_3d")
    artwork_3d_path = artwork_3d_path[:-4] + "png"

    if os.path.exists(artwork_3d_path):

        open_style_win = get_style_win_name(style) + "-artwork-3d"
        # 重复打开时，窗口置顶并直接返回
        if open_style_win in open_style_wins:
            # 判断窗口是否存在
            if open_style_wins[open_style_win].winfo_exists():
                set_window_top(open_style_wins[open_style_win])
                return "break"
            del open_style_wins[open_style_win]

        style_artwork_3d_win_frame = creat_Toplevel(open_style_win, x=770, y=150)
        set_window_icon(style_artwork_3d_win_frame, team.logo_path)
        open_style_wins[open_style_win] = style_artwork_3d_win_frame

        displayer = ArtworkDisplayerHeight(style_artwork_3d_win_frame, artwork_3d_path, 710, 0)

        # 窗口关闭时清理
        style_artwork_3d_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (style_win_closing(style_artwork_3d_win_frame)))

    else:
        return


