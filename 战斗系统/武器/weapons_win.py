
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from window import set_window_icon_webp, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

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

def creat_weapon_win(event, parent_frame, weapon):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(weapon.name, __name__):
        win_set_top(weapon.name, __name__)
        return "break"

    weapon_win_frame = creat_Toplevel(weapon.name, 540, 200, 300, 280)
    # 配置 weapon_win_frame 的布局
    weapon_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    weapon_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(weapon_win_frame, weapon.path)
    win_open_manage(weapon_win_frame, __name__)

    weapon_frame = ttk.Labelframe(weapon_win_frame, text=weapon.name)
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
    weapon_frame.bind("<Button-1>", win_set_top(weapon_frame, __name__))
    # 窗口关闭时清理
    weapon_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(weapon_frame, __name__))

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
        weapon_frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=weapon_name)
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
