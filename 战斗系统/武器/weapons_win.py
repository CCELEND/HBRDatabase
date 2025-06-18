
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from window import set_window_icon_webp, creat_Toplevel, set_window_top

from 武器.weapons_info import get_all_weapon_obj
import 武器.weapons_info

# 绑定武器 canvas 的事件
def bind_weapon_canvas(parent_frame, weapon, x, y):

    photo = get_photo(weapon.path, (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_weapon_win, parent_frame=parent_frame, 
        weapon=weapon)

open_weapon_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def weapon_win_closing(parent_frame):

    open_weapon_win = parent_frame.title()
    while open_weapon_win in open_weapon_wins:
        del open_weapon_wins[open_weapon_win]

    parent_frame.destroy()  # 销毁窗口

def creat_weapon_win(event, parent_frame, weapon):

    # 重复打开时，窗口置顶并直接返回
    if weapon.name in open_weapon_wins:
        # 判断窗口是否存在
        if open_weapon_wins[weapon.name].winfo_exists():
            set_window_top(open_weapon_wins[weapon.name])
            return "break"
        del open_weapon_wins[weapon.name]


    weapon_win_frame = creat_Toplevel(weapon.name, 540, 200, 300, 280)
    # 配置 weapon_win_frame 的布局
    weapon_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    weapon_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(weapon_win_frame, weapon.path)
    open_weapon_wins[weapon.name] = weapon_win_frame

    weapon_frame = ttk.LabelFrame(weapon_win_frame, text=weapon.name)
    weapon_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 weapon_frame 的布局
    weapon_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    weapon_frame.grid_columnconfigure(0, weight=3)  # 描述列
    weapon_frame.grid_columnconfigure(1, weight=1)  # hit

    desc_label = ttk.Label(weapon_frame, text=weapon.description, anchor="center")
    desc_label.grid(row=0, column=0, sticky="nsew")

    hit_label = ttk.Label(weapon_frame, text=weapon.hit, anchor="center")
    hit_label.grid(row=0, column=1, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    weapon_win_frame.bind("<Button-1>", lambda event: set_window_top(weapon_win_frame))
    # 窗口关闭时清理
    weapon_win_frame.protocol("WM_DELETE_WINDOW", lambda: weapon_win_closing(weapon_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_weapon(scrollbar_frame_obj):

    get_all_weapon_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    weapon_column_count = 0
    for weapon_num, weapon_name in enumerate(武器.weapons_info.weapons):
        weapon = 武器.weapons_info.weapons[weapon_name]

        # 武器
        weapon_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=weapon_name)
        bind_weapon_canvas(weapon_frame, weapon, 0, 0)

        # 计算行和列的位置
        weapon_row = weapon_num // 3  # 每3个换行
        weapon_column = weapon_num % 3  # 列位置
        weapon_frame.grid(row=weapon_row, column=weapon_column, padx=(10,0), pady=(0,5), sticky="nsew") #
        weapon_column_count += 1  # 更新列计数器
        if weapon_column_count == 3:  # 如果已经到达第3列，重置列计数器并增加行
            weapon_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
