
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

main_props_dir = {}
# 加载资源文件
def load_resources():
    global main_props_dir
    if main_props_dir:
        return
    main_props_dir = load_json("./持有物/主线道具/main_props.json")

# 加载图片并显示的函数
def show_main_props(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, main_props_dir)

    scrollbar_frame_obj.update_canvas()



