
# import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from PIL import Image, ImageTk
from canvas_events import get_photo, create_canvas_with_image

# 图片背景路径
base_path = "./持有物/图片背景/ThumbnailBase.webp"
halo_path = "./持有物/图片背景/ThumbnailHalo.webp"

# 加载图片并显示的函数
def show_holding(parent_frame, data_dir):

    # 图片大小
    base_size = (100, 100)
    halo_size = (96, 96)
    item_size = (66, 66)#(70,70)

    # 获取 Base 图对象
    base_photo = get_photo(base_path, base_size)
    # 获取 Halo 图对象
    halo_photo = get_photo(halo_path, halo_size)

    # 循环创建每一行
    for i, item in enumerate(data_dir):

        # 使用 LabelFrame 作为每一行的容器
        row_frame = ttk.LabelFrame(parent_frame, text=item)
        row_frame.grid(row=i, column=0, columnspan=6, padx=10, pady=(0,5), sticky="nsew")
        row_frame.grid_columnconfigure(0, weight=1)  # 让 inner_frame 适应 row_frame
     
        # 创建 inner_frame 让 Canvas 和 Label 并排
        inner_frame = ttk.Frame(row_frame)
        inner_frame.grid(row=0, column=0, columnspan=6, sticky="nsew")
        inner_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        inner_frame.grid_columnconfigure(0, weight=1)  # Canvas 列
        inner_frame.grid_columnconfigure(1, weight=3)  # 右侧信息列，权重更大以填充更多空间
        
        # 获取 item 图对象
        item_photo = get_photo(data_dir[item]["path"], item_size)
        # 左侧 Canvas（放图片）
        row_canvas = create_canvas_with_image(inner_frame, base_photo, 
            base_size[0], base_size[1], 0, 0, 0, 0, padx=10, pady=5)
        # 设置 Base 图坐标
        row_canvas.create_image(0, 0, anchor="nw", image=base_photo)
        # 设置 Halo 图坐标
        row_canvas.create_image(2, 2, anchor="nw", image=halo_photo)  # `z-index` 高于 Base
        # 设置 item 图坐标（70x70 居中）
        row_canvas.create_image(17, 17, anchor="nw", image=item_photo)

        # 右侧信息 Frame（放描述和价格和获取地点）
        info_frame = ttk.Frame(inner_frame)
        info_frame.grid(row=0, column=1, sticky="nsew")
        # 让 info_frame 内部组件垂直居中 3 1 3
        info_frame.grid_rowconfigure(0, weight=1) # 确保行填充
        info_frame.grid_columnconfigure(0, weight=3, minsize=300)  # 描述列
        info_frame.grid_columnconfigure(1, weight=1, minsize=100)  # 价格列
        info_frame.grid_columnconfigure(2, weight=3, minsize=300)  # 位置列
        
        # 右侧 Label（放文字描述）
        # 控制多行文本的对齐方式（仅影响 wraplength 设定的换行文本）justify="left"
        # 控制整个 Label 内的文本对齐方式（w 代表靠左对齐）anchor="w"
        desc_label = ttk.Label(info_frame, text=data_dir[item]["description"], justify="left", anchor="w")
        desc_label.grid(row=0, column=0, sticky="nsew")

        # 右侧 Label（放价格）right fg="red"背景色
        price_label = ttk.Label(info_frame, text=data_dir[item]['price'], justify="left", anchor="w")
        price_label.grid(row=0, column=1, sticky="nsew")

        # 右侧 Label（放获取位置）
        location_label = ttk.Label(info_frame, text=data_dir[item]['location'], justify="left", anchor="w")
        location_label.grid(row=0, column=2, sticky="nsew")





