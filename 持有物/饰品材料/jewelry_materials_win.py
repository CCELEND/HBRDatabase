
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

jewelry_materials_dir = {}
# 加载资源文件
def load_resources():
    global jewelry_materials_dir
    if jewelry_materials_dir:
        return
    jewelry_materials_dir = load_json("./持有物/饰品材料/jewelry_materials.json")

# 加载图片并显示的函数
def show_jewelry_materials(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, jewelry_materials_dir)

    scrollbar_frame_obj.update_canvas()



