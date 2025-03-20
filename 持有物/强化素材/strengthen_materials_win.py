
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

strengthen_materials_dir = {}
# 加载资源文件
def load_resources():
    global strengthen_materials_dir
    if strengthen_materials_dir:
        return
    strengthen_materials_dir = load_json("./持有物/强化素材/strengthen_materials.json")

# 加载图片并显示的函数
def show_strengthen_materials(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, strengthen_materials_dir)

    scrollbar_frame_obj.update_canvas()



