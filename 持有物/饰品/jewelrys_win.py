import sys
import os
import tkinter as tk
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon_webp, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

from 饰品.jewelrys_info import get_all_jewelry_obj
import 饰品.jewelrys_info

# 绑定饰品 canvas 的事件
def bind_jewelry_canvas(parent_frame, jewelry, x, y):

    photo = get_photo(jewelry.path, (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_jewelry_win, parent_frame=parent_frame, 
        jewelry=jewelry)

open_jewelry_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def jewelry_win_closing(parent_frame):

    open_jewelry_win = parent_frame.title()
    while open_jewelry_win in open_jewelry_wins:
        del open_jewelry_wins[open_jewelry_win]

    parent_frame.destroy()  # 销毁窗口

def creat_jewelry_win(event, parent_frame, jewelry):

    # 重复打开时，窗口置顶并直接返回
    if jewelry.name in open_jewelry_wins:
        # 判断窗口是否存在
        if open_jewelry_wins[jewelry.name].winfo_exists():
            set_window_top(open_jewelry_wins[jewelry.name])
            return "break"
        del open_jewelry_wins[jewelry.name]


    jewelry_win_frame = creat_Toplevel(parent_frame, jewelry.name, 540, 200, 440, 50)
    # 配置 jewelry_win_frame 的布局
    jewelry_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    jewelry_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(jewelry_win_frame, jewelry.path)
    open_jewelry_wins[jewelry.name] = jewelry_win_frame

    jewelry_frame = tk.LabelFrame(jewelry_win_frame, text=jewelry.name)
    jewelry_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 jewelry_frame 的布局
    jewelry_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    jewelry_frame.grid_columnconfigure(0, weight=3)  # 描述列
    jewelry_frame.grid_columnconfigure(1, weight=1)  # hit

    desc_label = tk.Label(jewelry_frame, text=jewelry.description, justify="left")
    desc_label.grid(row=0, column=0, sticky="nsew")

    hit_label = tk.Label(jewelry_frame, text=jewelry.hit, justify="left")
    hit_label.grid(row=0, column=1, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    jewelry_win_frame.bind("<Button-1>", lambda event: set_window_top(jewelry_win_frame))
    # 窗口关闭时清理
    jewelry_win_frame.protocol("WM_DELETE_WINDOW", lambda: jewelry_win_closing(jewelry_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_jewelry(scrollbar_frame_obj):

    get_all_jewelry_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    jewelry_column_count = 0
    for jewelry_num, jewelry_name in enumerate(饰品.jewelrys_info.jewelrys):
        jewelry = 饰品.jewelrys_info.jewelrys[jewelry_name]

        # 饰品
        jewelry_frame = tk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=jewelry_name)
        bind_jewelry_canvas(jewelry_frame, jewelry, 0, 0)

        # 计算行和列的位置
        jewelry_row = jewelry_num // 4  # 每4个换行
        jewelry_column = jewelry_num % 4  # 列位置
        jewelry_frame.grid(row=jewelry_row, column=jewelry_column, padx=(10,0), pady=(0,5), sticky="nsew") #
        jewelry_column_count += 1  # 更新列计数器
        if jewelry_column_count == 4:  # 如果已经到达第3列，重置列计数器并增加行
            jewelry_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
