
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

amplifiers_dir = {}
# 加载资源文件
def load_resources():
    global amplifiers_dir
    if amplifiers_dir:
        return
    amplifiers_dir = load_json("./持有物/增幅器/amplifiers.json")

# 加载图片并显示的函数
def show_amplifiers(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, amplifiers_dir)

    scrollbar_frame_obj.update_canvas()



