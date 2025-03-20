
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

currencys_dir = {}
# 加载资源文件
def load_resources():
    global currencys_dir
    if currencys_dir:
        return
    currencys_dir = load_json("./持有物/货币/currencys.json")

# 加载图片并显示的函数
def show_currencys(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, currencys_dir)

    scrollbar_frame_obj.update_canvas()



