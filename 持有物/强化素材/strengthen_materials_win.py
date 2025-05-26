
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json
from holding_win import show_holding

import 强化素材.strengthen_materials

# 加载图片并显示的函数
def show_strengthen_materials(scrollbar_frame_obj):

    强化素材.strengthen_materials.load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, 强化素材.strengthen_materials.strengthen_materials_dir)

    scrollbar_frame_obj.update_canvas()



