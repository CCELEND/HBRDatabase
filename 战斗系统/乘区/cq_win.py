import sys
import os
import tkinter as tk
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

open_cq_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def cq_win_closing(parent_frame):

    open_cq_win = parent_frame.title()
    while open_cq_win in open_cq_wins:
        del open_cq_wins[open_cq_win]

    parent_frame.destroy()  # 销毁窗口

def creat_cq_win(parent_frame):

    cq_logo_path = "./战斗系统/乘区/乘区.ico"
    cq_img_path = "./战斗系统/乘区/乘区.png"

    # 重复打开时，窗口置顶并直接返回
    if '乘区' in open_cq_wins:
        # 判断窗口是否存在
        if open_cq_wins['乘区'].winfo_exists():
            set_window_top(open_cq_wins['乘区'])
            return "break"
        del open_cq_wins['乘区']

    cq_win_frame = creat_Toplevel(parent_frame, '乘区', 820, 500, 440, 50)
    set_window_icon(cq_win_frame, cq_logo_path)
    open_cq_wins['乘区'] = cq_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    cq_image_viewer = ImageViewerWithScrollbar(cq_win_frame, 820, 500, cq_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    cq_win_frame.bind("<Button-1>", lambda event: set_window_top(cq_win_frame))
    # 窗口关闭时清理
    cq_win_frame.protocol("WM_DELETE_WINDOW", lambda: cq_win_closing(cq_win_frame))

    return "break"  # 阻止事件冒泡

