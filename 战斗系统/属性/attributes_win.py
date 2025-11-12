
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from window import set_window_icon_webp, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

from 属性.attributes_info import get_all_attribute_obj
import 属性.attributes_info

# 绑定属性 canvas 的事件
def bind_attribute_canvas(parent_frame, attribute, x, y):

    photo = get_photo(attribute.path, (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_attribute_win, parent_frame=parent_frame, 
        attribute=attribute)

def creat_attribute_win(event, parent_frame, attribute):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(attribute.name, __name__):
        win_set_top(attribute.name, __name__)
        return "break"

    attribute_win_frame = creat_Toplevel(attribute.name, 540, 200, 300, 280)
    # 配置 attribute_win_frame 的布局
    attribute_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    attribute_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(attribute_win_frame, attribute.path)
    win_open_manage(attribute_win_frame, __name__)

    attribute_frame = ttk.Labelframe(attribute_win_frame, text=attribute.name)
    attribute_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 attribute_frame 的布局
    attribute_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    attribute_frame.grid_columnconfigure(0, weight=1)  # 描述列

    info_label = ttk.Label(attribute_frame, text=attribute.description, anchor="center")
    info_label.grid(row=0, column=0, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    attribute_frame.bind("<Button-1>", win_set_top(attribute_frame, __name__))
    # 窗口关闭时清理
    attribute_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(attribute_frame, __name__))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_attribute(scrollbar_frame_obj):

    get_all_attribute_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    attribute_column_count = 0
    for attribute_num, attribute_name in enumerate(属性.attributes_info.attributes):
        attribute = 属性.attributes_info.attributes[attribute_name]

        # 属性
        attribute_frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=attribute_name)
        bind_attribute_canvas(attribute_frame, attribute, 0, 0)

        # 计算行和列的位置
        attribute_row = attribute_num // 4  # 每4个换行
        attribute_column = attribute_num % 4  # 列位置
        attribute_frame.grid(row=attribute_row, column=attribute_column, padx=(10,0), pady=(0,5), sticky="nsew") #
        attribute_column_count += 1  # 更新列计数器
        if attribute_column_count == 4:  # 如果已经到达第4列，重置列计数器并增加行
            attribute_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
