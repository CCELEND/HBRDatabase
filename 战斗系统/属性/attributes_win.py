import sys
import os
import tkinter as tk
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon_webp, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

from 属性.attributes_info import get_all_attribute_obj
import 属性.attributes_info

# 绑定属性 canvas 的事件
def bind_attribute_canvas(parent_frame, attribute, x, y):

    photo = get_photo(attribute.path, (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_attribute_win, parent_frame=parent_frame, 
        attribute=attribute)

open_attribute_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def attribute_win_closing(parent_frame):

    open_attribute_win = parent_frame.title()
    while open_attribute_win in open_attribute_wins:
        del open_attribute_wins[open_attribute_win]

    parent_frame.destroy()  # 销毁窗口

def creat_attribute_win(event, parent_frame, attribute):

    # 重复打开时，窗口置顶并直接返回
    if attribute.name in open_attribute_wins:
        # 判断窗口是否存在
        if open_attribute_wins[attribute.name].winfo_exists():
            set_window_top(open_attribute_wins[attribute.name])
            return "break"
        del open_attribute_wins[attribute.name]


    attribute_win_frame = creat_Toplevel(parent_frame, attribute.name, 540, 200, 440, 50)
    # 配置 attribute_win_frame 的布局
    attribute_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    attribute_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(attribute_win_frame, attribute.path)
    open_attribute_wins[attribute.name] = attribute_win_frame

    attribute_frame = tk.LabelFrame(attribute_win_frame, text=attribute.name)
    attribute_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 attribute_frame 的布局
    attribute_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    attribute_frame.grid_columnconfigure(0, weight=1)  # 描述列

    info_label = tk.Label(attribute_frame, text=attribute.description, justify="left")
    info_label.grid(row=0, column=0, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    attribute_win_frame.bind("<Button-1>", lambda event: set_window_top(attribute_win_frame))
    # 窗口关闭时清理
    attribute_win_frame.protocol("WM_DELETE_WINDOW", lambda: attribute_win_closing(attribute_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_attribute(scrollbar_frame_obj):

    get_all_attribute_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    attribute_column_count = 0
    for attribute_num, attribute_name in enumerate(属性.attributes_info.attributes):
        attribute = 属性.attributes_info.attributes[attribute_name]

        # 属性
        attribute_frame = tk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=attribute_name)
        bind_attribute_canvas(attribute_frame, attribute, 0, 0)

        # 计算行和列的位置
        attribute_row = attribute_num // 4  # 每4个换行
        attribute_column = attribute_num % 4  # 列位置
        attribute_frame.grid(row=attribute_row, column=attribute_column, padx=(10,0), pady=(0,5), sticky="nsew") #
        attribute_column_count += 1  # 更新列计数器
        if attribute_column_count == 4:  # 如果已经到达第4列，重置列计数器并增加行
            attribute_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
