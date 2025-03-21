import sys
import os
import tkinter as tk
from PIL import Image, ImageTk

from canvas_events import bind_canvas_events, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

open_jc_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def jc_win_closing(parent_frame):

    open_jc_win = parent_frame.title()
    while open_jc_win in open_jc_wins:
        del open_jc_wins[open_jc_win]

    parent_frame.destroy()  # 销毁窗口

def creat_jc_win(parent_frame):

    jc_logo_path = "./help.ico"
    jc_img_path = "./战斗系统/基础/基础.png"

    # 重复打开时，窗口置顶并直接返回
    if '基础' in open_jc_wins:
        # 判断窗口是否存在
        if open_jc_wins['基础'].winfo_exists():
            set_window_top(open_jc_wins['基础'])
            return "break"
        del open_jc_wins['基础']

    jc_win_frame = creat_Toplevel(parent_frame, '基础', 600, 840, 440, 50)
    set_window_icon(jc_win_frame, jc_logo_path)
    open_jc_wins['基础'] = jc_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    jc_image_viewer = ImageViewerWithScrollbar(jc_win_frame, 600, 840, jc_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    jc_win_frame.bind("<Button-1>", lambda event: set_window_top(jc_win_frame))
    # 窗口关闭时清理
    jc_win_frame.protocol("WM_DELETE_WINDOW", lambda: jc_win_closing(jc_win_frame))

    return "break"  # 阻止事件冒泡

