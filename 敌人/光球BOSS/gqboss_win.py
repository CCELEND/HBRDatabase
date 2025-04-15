import sys
import os
# import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

from tools import load_json
from 光球BOSS.gqboss_info import gqbosss, get_all_gqboss_obj

gqbosss_json = {}
# 加载资源文件
def load_resources():
    global gqbosss_json
    if gqbosss_json:
        return
    gqbosss_json = load_json("./敌人/光球BOSS/gqboss.json")

# 绑定光球BOSS canvas 的事件
def bind_gqboss_canvas(parent_frame, gqboss, x, y):

    photo = get_photo(gqboss.img_path, (90, 90))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 130, 130, 20, 20, x, y)
    mouse_bind_canvas_events(canvas)

    if gqboss.guide_path:
        bind_canvas_events(canvas, 
            creat_gqboss_win, parent_frame=parent_frame, 
            gqboss=gqboss)

open_gqboss_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def gqboss_win_closing(parent_frame):

    open_gqboss_win = parent_frame.title()
    while open_gqboss_win in open_gqboss_wins:
        del open_gqboss_wins[open_gqboss_win]

    parent_frame.destroy()  # 销毁窗口

def creat_gqboss_win(event, parent_frame, gqboss):

    # 重复打开时，窗口置顶并直接返回
    if gqboss.name in open_gqboss_wins:
        # 判断窗口是否存在
        if open_gqboss_wins[gqboss.name].winfo_exists():
            set_window_top(open_gqboss_wins[gqboss.name])
            return "break"
        del open_gqboss_wins[gqboss.name]

    if "攻略" in gqboss.name:
        gqboss_win_frame = creat_Toplevel(gqboss.name, 600, 840, 440, 50)
    else:
        gqboss_win_frame = creat_Toplevel(gqboss.name, 600, 840, 440, 50)
    set_window_icon(gqboss_win_frame, gqboss.logo_path)
    open_gqboss_wins[gqboss.name] = gqboss_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    gqboss_image_viewer = ImageViewerWithScrollbar(gqboss_win_frame, 600, 840, gqboss.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    gqboss_win_frame.bind("<Button-1>", lambda event: set_window_top(gqboss_win_frame))
    # 窗口关闭时清理
    gqboss_win_frame.protocol("WM_DELETE_WINDOW", lambda: gqboss_win_closing(gqboss_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_gqboss_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_gqboss_obj(gqbosss_json)

    global gqbosss

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, gqboss_name in enumerate(gqbosss):
        # 光球BOSS敌人对象
        gqboss = gqbosss[gqboss_name]

        gqboss_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=gqboss_name)
        bind_gqboss_canvas(gqboss_frame, gqboss, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        gqboss_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        gqboss_frame.grid_rowconfigure(0, weight=1)
        gqboss_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
