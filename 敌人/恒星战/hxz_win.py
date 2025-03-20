import sys
import os
import tkinter as tk
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

from tools import load_json
from 恒星战.hxz_info import hxzs, get_all_hxz_obj

# 图片背景路径
base_path = "./敌人/恒星战/dimensionClassFrameL.webp"

hxzs_json = {}
# 加载资源文件
def load_resources():
    global hxzs_json
    if hxzs_json:
        return
    hxzs_json = load_json("./敌人/恒星战/hxz.json")

open_hxz_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def hxz_win_closing(parent_frame):

    open_hxz_win = parent_frame.title()
    while open_hxz_win in open_hxz_wins:
        del open_hxz_wins[open_hxz_win]

    parent_frame.destroy()  # 销毁窗口

def creat_hxz_win(event, parent_frame, hxz):

    # 重复打开时，窗口置顶并直接返回
    if hxz.name in open_hxz_wins:
        # 判断窗口是否存在
        if open_hxz_wins[hxz.name].winfo_exists():
            set_window_top(open_hxz_wins[hxz.name])
            return "break"
        del open_hxz_wins[hxz.name]

    if "攻略" in hxz.name:
        hxz_win_frame = creat_Toplevel(parent_frame, hxz.name, 600, 840, 440, 50)
    else:
        hxz_win_frame = creat_Toplevel(parent_frame, hxz.name, 1280, 720, 440, 50)
    set_window_icon(hxz_win_frame, hxz.logo_path)
    open_hxz_wins[hxz.name] = hxz_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    hxz_image_viewer = ImageViewerWithScrollbar(hxz_win_frame, 1280, 720, hxz.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    hxz_win_frame.bind("<Button-1>", lambda event: set_window_top(hxz_win_frame))
    # 窗口关闭时清理
    hxz_win_frame.protocol("WM_DELETE_WINDOW", lambda: hxz_win_closing(hxz_win_frame))

    return "break"  # 阻止事件冒泡

# 加载图片并显示的函数
def show_hxz_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_hxz_obj(hxzs_json)

    global hxzs

    base_size = (100, 100)
    enemy_size = (86, 86)

    # 获取 Base 图对象
    base_photo = get_photo(base_path, base_size)

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, hxz_name in enumerate(hxzs):
        # 恒星战敌人对象
        hxz = hxzs[hxz_name]

        hxz_frame = tk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=hxz_name)
        photo = get_photo(hxz.img_path, (128, 72))
        canvas = create_canvas_with_image(hxz_frame, 
            photo, 130, 130, 1, 29, 0, 0)

        base_canvas = create_canvas_with_image(hxz_frame, 
            base_photo, 130, 130, 0, 15, 0, 1)
        enemy_photo = get_photo(hxz.img_path_enemy, enemy_size)
        base_canvas.create_image(7, 22, anchor="nw", image=enemy_photo)
        mouse_bind_canvas_events(base_canvas)
        if hxz.guide_path:
            bind_canvas_events(base_canvas, 
                creat_hxz_win, parent_frame=hxz_frame, 
                hxz=hxz)


        # 计算行和列的位置
        row = i // 3  # 每3个换行
        column = i % 3  # 列位置
        hxz_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        hxz_frame.grid_rowconfigure(0, weight=1)
        hxz_frame.grid_columnconfigure(0, weight=1)
        hxz_frame.grid_columnconfigure(1, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 3:  # 如果已经到达第3列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
