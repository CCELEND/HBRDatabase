
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_win import ScrollbarFrameWin

from 饰品.jewelrys_info import get_jewelrys_obj, load_type_resources
from 饰品.光球.orbs_skill_win import creat_orb_skill_win
import 饰品.jewelrys_info
import 持有物.holding_win


# 加载图片并显示饰品的函数
def show_jewelrys(scrollbar_frame_obj, jewelrys):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    # 图片大小
    base_size = (100, 100)
    halo_size = (96, 96)
    jewelry_size = (80, 80)

    # 获取 Base 图对象
    base_photo = get_photo(持有物.holding_win.base_path, base_size)
    # 获取 Halo 图对象
    halo_photo = get_photo(持有物.holding_win.halo_path, halo_size)

    # 循环创建每一行，遍历得到饰品对象
    for i, jewelry_name in enumerate(jewelrys):
        jewelry = jewelrys[jewelry_name]

        # 使用 LabelFrame 作为每一行的容器
        row_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=jewelry.name)
        row_frame.grid(row=i, column=0, columnspan=6, padx=10, pady=(0,10), sticky="nsew")
        row_frame.grid_columnconfigure(0, weight=1)  # 让 inner_frame 适应 row_frame
     
        # 创建 inner_frame 让 Canvas 和 Label 并排
        inner_frame = ttk.Frame(row_frame)
        inner_frame.grid(row=0, column=0, columnspan=6, sticky="nsew")
        inner_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        inner_frame.grid_columnconfigure(0, weight=1)  # Canvas 列
        inner_frame.grid_columnconfigure(1, weight=4)  # 右侧信息列，权重更大以填充更多空间
        
        # 获取 jewelry 图对象
        jewelry_photo = get_photo(jewelry.path, jewelry_size)
        # 左侧 Canvas（放图片）
        row_canvas = create_canvas_with_image(inner_frame, base_photo, 
            base_size[0], base_size[1], 0, 0, 0, 0, padx=10, pady=5)
        # 设置 Base 图坐标
        row_canvas.create_image(0, 0, anchor="nw", image=base_photo)
        # 设置 Halo 图坐标
        row_canvas.create_image(2, 2, anchor="nw", image=halo_photo)  # `z-index` 高于 Base
        # 设置 jewelry 图坐标（70x70 居中）
        row_canvas.create_image(10, 10, anchor="nw", image=jewelry_photo)

        if jewelry.type == "光球":
            mouse_bind_canvas_events(row_canvas)
            bind_canvas_events(row_canvas, creat_orb_skill_win, parent_frame=row_frame, orb=jewelry)

        # 右侧信息 Frame（放描述和价格和获取地点）
        info_frame = ttk.Frame(inner_frame)
        info_frame.grid(row=0, column=1, sticky="nsew")
        # 让 info_frame 内部组件垂直居中 3 1 3
        info_frame.grid_rowconfigure(0, weight=1) # 确保行填充
        info_frame.grid_columnconfigure(0, weight=4, minsize=450)  # 描述列
        info_frame.grid_columnconfigure(1, weight=1, minsize=150)  # 稀有度列
        info_frame.grid_columnconfigure(2, weight=2, minsize=200)  # 位置列
        
        # 右侧 Label（放文字描述）
        # 控制多行文本的对齐方式（仅影响 wraplength 设定的换行文本）justify="left"
        # 控制整个 Label 内的文本对齐方式（w 代表靠左对齐）anchor="w"
        desc_label = ttk.Label(info_frame, text=jewelry.description, justify="left", anchor="w")
        desc_label.grid(row=0, column=0, sticky="nsew")

        # 右侧 Label（放稀有度）right fg="red"背景色
        rarity_label = ttk.Label(info_frame, text=int(jewelry.rarity)*"★", justify="left", anchor="w")
        rarity_label.grid(row=0, column=1, sticky="nsew")

        # 右侧 Label（放获取位置）
        location_label = ttk.Label(info_frame, text=jewelry.location, justify="left", anchor="w") #, anchor="e"
        location_label.grid(row=0, column=2, sticky="nsew")

    scrollbar_frame_obj.update_canvas()


# 绑定饰品 canvas 的事件
def bind_jewelry_type_canvas(parent_frame, jewelry_type_json, x, y):

    photo = get_photo(jewelry_type_json['img_path'], (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_jewelrys_win, parent_frame=parent_frame, 
        jewelry_type_json=jewelry_type_json)

# 创建饰品窗口
def creat_jewelrys_win(event, parent_frame, jewelry_type_json):

    jewelry_win_name = jewelry_type_json['name']

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(jewelry_win_name, __name__):
        win_set_top(jewelry_win_name, __name__)
        return "break"

    jewelrys = get_jewelrys_obj(jewelry_type_json)

    jewelry_win_frame = creat_Toplevel(jewelry_win_name, 1040, 800, 240, 80)
    # 配置 jewelry_win_frame 的布局
    logo_path = jewelry_type_json['logo_path']
    set_window_icon(jewelry_win_frame, logo_path)
    set_window_expand(jewelry_win_frame, rowspan=1, columnspan=2)

    win_open_manage(jewelry_win_frame, __name__)

    scrollbar_frame_obj = ScrollbarFrameWin(jewelry_win_frame, columnspan=2)
    show_jewelrys(scrollbar_frame_obj, jewelrys)


    # 绑定鼠标点击事件到父窗口，点击置顶
    jewelry_win_frame.bind("<Button-1>", win_set_top(jewelry_win_frame, __name__))
    # 窗口关闭时清理
    jewelry_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(jewelry_win_frame, __name__))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_jewelrys_type(scrollbar_frame_obj):

    # get_all_jewelry_obj()

    load_type_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    jewelry_type_column_count = 0
    for jewelry_type_num, jewelry_type_name in enumerate(饰品.jewelrys_info.jewelrys_type_json):
        jewelry_type_json = 饰品.jewelrys_info.jewelrys_type_json[jewelry_type_name]

        # 饰品类型
        jewelry_type_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=jewelry_type_name)
        bind_jewelry_type_canvas(jewelry_type_frame, jewelry_type_json, 0, 0)

        # 计算行和列的位置
        jewelry_type_row = jewelry_type_num // 4  # 每4个换行
        jewelry_type_column = jewelry_type_num % 4  # 列位置
        jewelry_type_frame.grid(row=jewelry_type_row, column=jewelry_type_column, padx=(10,0), pady=(0,5), sticky="nsew") #
        jewelry_type_column_count += 1  # 更新列计数器
        if jewelry_type_column_count == 4:  # 如果已经到达第3列，重置列计数器并增加行
            jewelry_type_column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
