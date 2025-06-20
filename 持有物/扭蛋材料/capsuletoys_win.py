
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events

from tools import load_json
import 持有物.holding_win

capsuletoys_json = {}
# 加载资源文件
def load_resources():
    global capsuletoys_json
    if capsuletoys_json:
        return
    capsuletoys_json = load_json("./持有物/扭蛋材料/capsuletoys.json")

# 加载图片并显示的函数
def show_capsuletoys(scrollbar_frame_obj):

    load_resources()

    # 图片大小
    base_size = (100, 100)
    halo_size = (96, 96)
    item_size = (80, 80)

    # 获取 Base 图对象
    base_photo = get_photo(持有物.holding_win.base_path, base_size)
    # 获取 Halo 图对象
    halo_photo = get_photo(持有物.holding_win.halo_path, halo_size)

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, capsuletoy_name in enumerate(capsuletoys_json):

        # 获取 item 图对象
        item_photo = get_photo(capsuletoys_json[capsuletoy_name]["path"], item_size)

        capsuletoy_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=capsuletoy_name)

        # Canvas
        canvas = create_canvas_with_image(capsuletoy_frame, base_photo, 
            base_size[0], base_size[1], 0, 0, 0, 0, padx=10, pady=5)
        mouse_bind_canvas_events(canvas)
        # 设置 Base 图坐标
        canvas.create_image(0, 0, anchor="nw", image=base_photo)
        # 设置 Halo 图坐标
        canvas.create_image(2, 2, anchor="nw", image=halo_photo)  # `z-index` 高于 Base
        # 设置 item 图坐标（80x80 居中）
        canvas.create_image(10, 10, anchor="nw", image=item_photo)
        mouse_bind_canvas_events(canvas)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        capsuletoy_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        capsuletoy_frame.grid_rowconfigure(0, weight=1)
        capsuletoy_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
