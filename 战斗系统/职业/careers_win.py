
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from window import set_window_icon_webp, creat_Toplevel, set_window_top

from 职业.careers_info import get_all_career_obj
import 职业.careers_info

# 绑定职业 canvas 的事件
def bind_career_canvas(parent_frame, career, x, y):

    photo = get_photo(career.path, (200, 40))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 240, 40, 20, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_career_win, parent_frame=parent_frame, 
        career=career)

open_career_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def career_win_closing(parent_frame):

    open_career_win = parent_frame.title()
    while open_career_win in open_career_wins:
        del open_career_wins[open_career_win]

    parent_frame.destroy()  # 销毁窗口

def creat_career_win(event, parent_frame, career):

    # 重复打开时，窗口置顶并直接返回
    if career.name in open_career_wins:
        # 判断窗口是否存在
        if open_career_wins[career.name].winfo_exists():
            set_window_top(open_career_wins[career.name])
            return "break"
        del open_career_wins[career.name]


    career_win_frame = creat_Toplevel(career.name, 540, 200, 300, 280)
    # 配置 career_win_frame 的布局
    career_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    career_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(career_win_frame, career.path)
    open_career_wins[career.name] = career_win_frame

    career_frame = ttk.LabelFrame(career_win_frame, text=career.name)
    career_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 career_frame 的布局
    career_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    career_frame.grid_columnconfigure(0, weight=1)  # 描述列

    desc_label = ttk.Label(career_frame, text=career.description, anchor="center")
    desc_label.grid(row=0, column=0, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    career_win_frame.bind("<Button-1>", lambda event: set_window_top(career_win_frame))
    # 窗口关闭时清理
    career_win_frame.protocol("WM_DELETE_WINDOW", lambda: career_win_closing(career_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_career(scrollbar_frame_obj):

    get_all_career_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    career_column_count = 0
    for career_num, career_name in enumerate(职业.careers_info.careers):
        career = 职业.careers_info.careers[career_name]

        # 职业
        career_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=career_name)
        bind_career_canvas(career_frame, career, 0, 0)

        # 计算行和列的位置
        career_row = career_num // 3  # 每3个换行
        career_column = career_num % 3  # 列位置
        career_frame.grid(row=career_row, column=career_column, padx=(10,0), pady=(0,5), sticky="nsew") #
        career_column_count += 1  # 更新列计数器
        if career_column_count == 3:  # 如果已经到达第3列，重置列计数器并增加行
            career_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
