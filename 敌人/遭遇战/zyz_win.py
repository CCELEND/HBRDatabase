
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 遭遇战.zyz_info import zyzs, get_all_zyz_obj

zyzs_json = {}
# 加载资源文件
def load_resources():
    global zyzs_json
    if zyzs_json:
        return
    zyzs_json = load_json("./敌人/遭遇战/zyz.json")

# 绑定遭遇战 canvas 的事件
def bind_zyz_enemy_canvas(parent_frame, zyz, x, y):
    photo = get_photo(zyz.img_path, (128, 72))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 130, 130, 20, 29, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_zyz_enemy_win, parent_frame=parent_frame, 
        zyz=zyz)


def creat_zyz_enemy_win(event, parent_frame, zyz):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(zyz.name, __name__):
        win_set_top(zyz.name, __name__)
        return "break"
        
    zyz_win_frame = creat_Toplevel(zyz.name, 1280, 715, 180, 140)
    set_window_icon(zyz_win_frame, zyz.logo_path)
    win_open_manage(zyz_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    zyz_image_viewer = ImageViewerWithScrollbar(zyz_win_frame, 1280, 715, zyz.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    zyz_win_frame.bind("<Button-1>", win_set_top(zyz_win_frame, __name__))
    # 窗口关闭时清理
    zyz_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(zyz_win_frame, __name__, zyz_image_viewer))


    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_zyz_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_zyz_obj(zyzs_json)

    global zyzs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, zyz_name in enumerate(zyzs):
        # 遭遇战敌人对象
        zyz = zyzs[zyz_name]

        zyz_enemy_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=zyz_name)
        bind_zyz_enemy_canvas(zyz_enemy_frame, zyz, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        zyz_enemy_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        zyz_enemy_frame.grid_rowconfigure(0, weight=1)
        zyz_enemy_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
