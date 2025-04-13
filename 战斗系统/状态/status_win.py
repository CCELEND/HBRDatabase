import sys
import os
# import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon_webp, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin


from 状态.status_info import get_all_statu_obj
import 状态.status_info

# 绑定状态 canvas 的事件
def bind_statu_canvas(parent_frame, statu, x, y):

    photo = get_photo(statu.path, (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_statu_win, parent_frame=parent_frame, 
        statu=statu)

open_statu_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def statu_win_closing(parent_frame):

    open_statu_win = parent_frame.title()
    while open_statu_win in open_statu_wins:
        del open_statu_wins[open_statu_win]

    parent_frame.destroy()  # 销毁窗口

def creat_statu_win(event, parent_frame, statu):

    # 重复打开时，窗口置顶并直接返回
    if statu.name in open_statu_wins:
        # 判断窗口是否存在
        if open_statu_wins[statu.name].winfo_exists():
            set_window_top(open_statu_wins[statu.name])
            return "break"
        del open_statu_wins[statu.name]


    statu_win_frame = creat_Toplevel(parent_frame, statu.name, 540, 200, 440, 50)
    # 配置 statu_win_frame 的布局
    statu_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    statu_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(statu_win_frame, statu.path)
    open_statu_wins[statu.name] = statu_win_frame

    statu_frame = ttk.LabelFrame(statu_win_frame, text=statu.name)
    statu_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 statu_frame 的布局
    statu_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    statu_frame.grid_columnconfigure(0, weight=3)  # 描述列
    statu_frame.grid_columnconfigure(1, weight=1)  # 叠加数列

    if statu.effect:
        info = statu.effect
    else:
        info = statu.description
    info_label = ttk.Label(statu_frame, text=info, anchor="center")
    info_label.grid(row=0, column=0, sticky="nsew")

    stack_label = ttk.Label(statu_frame, text=statu.stack, anchor="center")
    stack_label.grid(row=0, column=1, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    statu_win_frame.bind("<Button-1>", lambda event: set_window_top(statu_win_frame))
    # 窗口关闭时清理
    statu_win_frame.protocol("WM_DELETE_WINDOW", lambda: statu_win_closing(statu_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_statu(scrollbar_frame_obj):

    get_all_statu_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    for type_num, type in enumerate(状态.status_info.statu_categories):
        # 状态类型
        type_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=type+"类型状态")
        type_frame.grid(row=type_num, column=0, columnspan=6, padx=10, pady=(0,5), sticky="nsew") #

        series_column_count = 0
        for series_num, series in enumerate(状态.status_info.statu_categories[type]):
            # 所属系列
            series_frame = ttk.LabelFrame(type_frame, text=series)
            series_frame.grid(row=series_num, column=0, padx=(5,0), pady=(0,5), sticky="nesw")  # 设置间距

            statu_column_count = 0
            for statu_num, statu_name in enumerate(状态.status_info.statu_categories[type][series]):
                # 状态对象
                statu = 状态.status_info.statu_categories[type][series][statu_name]
                # print(statu.name)

                if len(状态.status_info.statu_categories[type][series]) == 1:
                    bind_statu_canvas(series_frame, statu, 0, 0)
                else:
                    statu_frame = ttk.LabelFrame(series_frame, text=statu_name)
                    bind_statu_canvas(statu_frame, statu, 0, 0)

                    if type in ['增益', '减益']:
                        # 计算行和列的位置
                        statu_row = statu_num // 4  # 每4个换行
                        statu_column = statu_num % 4  # 列位置
                        statu_frame.grid(row=statu_row, column=statu_column, padx=5, pady=(0,5), sticky="nesw")  # 设置间距
                        statu_column_count += 1  # 更新列计数器
                        if statu_column_count == 4:  # 如果已经到达第4列，重置列计数器并增加行
                            statu_column_count = 0 
                    else:
                        statu_frame.grid(row=0, column=statu_num, padx=5, pady=(0,5), sticky="nesw")  # 设置间距      

            if type in ['增益']:
                # 计算行和列的位置
                series_row = series_num // 3  # 每3个换行
                series_column = series_num % 3  # 列位置
                series_frame.grid(row=series_row, column=series_column, padx=(5,0), sticky="nesw")  # 设置间距
                series_column_count += 1  # 更新列计数器
                if series_column_count == 3:  # 如果已经到达第3列，重置列计数器并增加行
                    series_column_count = 0
            elif type in ['减益']:
                # 计算行和列的位置
                series_row = series_num // 4  # 每4个换行
                series_column = series_num % 4  # 列位置
                series_frame.grid(row=series_row, column=series_column, padx=(5,0), sticky="nesw")  # 设置间距
                series_column_count += 1  # 更新列计数器
                if series_column_count == 4:  # 如果已经到达第4列，重置列计数器并增加行
                    series_column_count = 0                
            elif type in ['其他']:
                # 计算行和列的位置
                series_row = series_num // 5  # 每5个换行
                series_column = series_num % 5  # 列位置
                series_frame.grid(row=series_row, column=series_column, padx=(5,0), sticky="nesw")  # 设置间距
                series_column_count += 1  # 更新列计数器
                if series_column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
                    series_column_count = 0
            else:
                series_frame.grid(row=0, column=series_num, padx=(5,0), sticky="nesw")  # 设置间距


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
