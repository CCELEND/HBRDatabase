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
from 时之修炼场.szxlc_info import szxlcs, get_all_szxlc_obj

szxlcs_json = {}
# 加载资源文件
def load_resources():
    global szxlcs_json
    if szxlcs_json:
        return
    szxlcs_json = load_json("./敌人/时之修炼场/szxlc.json")

# 绑定时之修炼场 canvas 的事件
def bind_szxlc_canvas(parent_frame, szxlc, x, y):

    photo = get_photo(szxlc.img_path, (90, 90))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 130, 130, 20, 20, x, y)
    mouse_bind_canvas_events(canvas)

    if szxlc.guide_path:
        bind_canvas_events(canvas, 
            creat_szxlc_win, parent_frame=parent_frame, 
            szxlc=szxlc)

open_szxlc_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def szxlc_win_closing(parent_frame):

    open_szxlc_win = parent_frame.title()
    while open_szxlc_win in open_szxlc_wins:
        del open_szxlc_wins[open_szxlc_win]

    parent_frame.destroy()  # 销毁窗口

def creat_szxlc_win(event, parent_frame, szxlc):

    # 重复打开时，窗口置顶并直接返回
    if szxlc.name in open_szxlc_wins:
        # 判断窗口是否存在
        if open_szxlc_wins[szxlc.name].winfo_exists():
            set_window_top(open_szxlc_wins[szxlc.name])
            return "break"
        del open_szxlc_wins[szxlc.name]


    szxlc_win_frame = creat_Toplevel(szxlc.name, 600, 840, 440, 50)
    set_window_icon(szxlc_win_frame, szxlc.logo_path)
    open_szxlc_wins[szxlc.name] = szxlc_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    szxlc_image_viewer = ImageViewerWithScrollbar(szxlc_win_frame, 600, 840, szxlc.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    szxlc_win_frame.bind("<Button-1>", lambda event: set_window_top(szxlc_win_frame))
    # 窗口关闭时清理
    szxlc_win_frame.protocol("WM_DELETE_WINDOW", lambda: szxlc_win_closing(szxlc_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_szxlc_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_szxlc_obj(szxlcs_json)

    global szxlcs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, szxlc_name in enumerate(szxlcs):
        # 时之修炼场敌人对象
        szxlc = szxlcs[szxlc_name]

        szxlc_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=szxlc_name)
        bind_szxlc_canvas(szxlc_frame, szxlc, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        szxlc_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        szxlc_frame.grid_rowconfigure(0, weight=1)
        szxlc_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
