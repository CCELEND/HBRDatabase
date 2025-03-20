
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

tickets_dir = {}
# 加载资源文件
def load_resources():
    global tickets_dir
    if tickets_dir:
        return
    tickets_dir = load_json("./持有物/入场券/tickets.json")

# 加载图片并显示的函数
def show_tickets(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, tickets_dir)

    scrollbar_frame_obj.update_canvas()



